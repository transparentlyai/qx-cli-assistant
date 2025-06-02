import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field, create_model
from rich.console import Console

from qx.core.paths import (
    PROJECT_MCP_SERVERS_PATH,
    SYSTEM_MCP_SERVERS_PATH,
    USER_MCP_SERVERS_PATH,
)

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = None


class MCPServersFileContent(BaseModel):
    mcpServers: Dict[str, MCPServerConfig]


class MCPManager:
    def __init__(self, console: Any, parent_task_group: Optional[anyio.abc.TaskGroup]):
        self.console = console
        self._parent_task_group = parent_task_group
        self._available_servers: Dict[str, MCPServerConfig] = {}
        self._active_sessions: Dict[str, ClientSession] = {}
        self._active_sessions_exit_stack: Dict[str, AsyncExitStack] = {}
        # Stores asyncio.Task objects for active MCP server management tasks
        self._active_tasks: Dict[str, asyncio.Task] = {}
        # Stores tools provided by each active server
        self._tools_by_server: Dict[
            str, List[Tuple[Callable, Dict[str, Any], Type[BaseModel]]]
        ] = {}

    def load_mcp_configs(self):
        """
        Loads and merges MCP server configurations from system, user, and project levels.
        Higher priority configurations overwrite lower priority ones.
        """
        config_paths = [
            SYSTEM_MCP_SERVERS_PATH,
            USER_MCP_SERVERS_PATH,
            PROJECT_MCP_SERVERS_PATH,
        ]

        for path in config_paths:
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding="utf-8")
                    data = json.loads(content)
                    parsed_config = MCPServersFileContent.model_validate(data)
                    self._available_servers.update(parsed_config.mcpServers)
                    logger.info(f"Loaded MCP configurations from {path}")
                except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
                    logger.warning(
                        f"Failed to load MCP configurations from {path}: {e}"
                    )
                    from rich.console import Console

                    Console().print(
                        f"[yellow]Warning:[/yellow] Failed to load MCP configurations from {path}: {e}"
                    )
            else:
                logger.debug(f"MCP configuration file not found at {path}")

        if not self._available_servers:
            logger.info("No MCP servers configured.")
        else:
            logger.info(
                f"Available MCP servers: {list(self._available_servers.keys())}"
            )

    def get_available_server_names(self) -> List[str]:
        """Returns a list of names of all available MCP servers."""
        return list(self._available_servers.keys())

    async def connect_server(self, server_name: str) -> bool:
        """
        Connects to a specified MCP server and registers its tools.
        Manages the connection within a dedicated AnyIO task.
        """
        if self._parent_task_group is None:
            from rich.console import Console

            Console().print(
                "[red]Error:[/red] MCPManager not initialized with a parent task group. Cannot connect."
            )
            return False

        if server_name not in self._available_servers:
            Console().print(
                f"[red]Error:[/red] MCP server '{server_name}' not found in configurations."
            )
            return False

        if server_name in self._active_tasks:  # Check _active_tasks for running session
            Console().print(
                f"[blue]Info:[/blue] MCP server '{server_name}' is already connected or connecting."
            )
            return True

        config = self._available_servers[server_name]
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )

        # This nested function is the coroutine run by the task group.
        # It captures 'self', 'server_name', and 'server_params' from the outer scope.
        async def _manage_session_task(*, task_status: anyio.abc.TaskStatus):
            task_object: Optional[asyncio.Task] = None
            try:
                # Assuming asyncio backend for AnyIO. This gets the asyncio.Task object.
                task_object = asyncio.current_task()
                if task_object is None:  # Should not happen in normal asyncio execution
                    raise RuntimeError(
                        "Could not retrieve current asyncio task object."
                    )
            except RuntimeError as e:
                logger.critical(
                    f"MCP task for '{server_name}': Failed to get task handle: {e}",
                    exc_info=True,
                )
                # TaskGroup.start will re-raise this if task_status.started() is not called.
                raise

            # Register the task object. It will be removed in the finally block.
            self._active_tasks[server_name] = task_object

            exit_stack = AsyncExitStack()
            # Store exit_stack under server_name to ensure it's closed if task exits unexpectedly
            self._active_sessions_exit_stack[server_name] = exit_stack

            try:
                stdio_transport = await exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                stdio_reader, stdio_writer = stdio_transport
                session = await exit_stack.enter_async_context(
                    ClientSession(stdio_reader, stdio_writer)
                )
                await session.initialize()

                self._active_sessions[server_name] = session  # Register session

                response = await session.list_tools()
                new_tools = []
                for mcp_tool in response.tools:
                    try:
                        qx_tool_func, qx_tool_schema, qx_tool_input_model = (
                            self._convert_mcp_tool_to_qx_format(session, mcp_tool)
                        )
                        new_tools.append(
                            (qx_tool_func, qx_tool_schema, qx_tool_input_model)
                        )
                        logger.info(
                            f"Converted tool '{mcp_tool.name}' from MCP server '{server_name}'."
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to convert or register tool '{mcp_tool.name}' from '{server_name}': {e}",
                            exc_info=True,
                        )
                        Console().print(
                            f"[red]Error:[/red] Failed to register tool '{mcp_tool.name}' from '{server_name}': {e}"
                        )

                self._tools_by_server[server_name] = (
                    new_tools  # Store tools for this server
                )

                Console().print(
                    f"[green]Success:[/green] Connected to MCP server '{server_name}' and loaded {len(new_tools)} tools."
                )

                task_status.started()  # Signal successful startup to TaskGroup.start()

                await anyio.sleep_forever()  # Keep the session alive until cancelled

            except asyncio.CancelledError:
                logger.info(
                    f"MCP session management task for '{server_name}' cancelled."
                )
            except Exception as e:
                logger.error(
                    f"Error in MCP session management task for '{server_name}': {e}",
                    exc_info=True,
                )
                Console().print(
                    f"[red]Error:[/red] MCP session for '{server_name}' encountered an error: {e}"
                )
                # If task_status.started() hasn't been called, TaskGroup.start() will raise this.
                # Otherwise, the TaskGroup's general error handling applies.
                if hasattr(task_status, "started") and not getattr(
                    task_status, "_started", False
                ):  # Check if started() was called
                    # Error occurred before startup was signaled.
                    pass  # Cleanup is handled in finally
                raise  # Re-raise for the TaskGroup or caller of start()
            finally:
                logger.info(f"Cleaning up MCP session for '{server_name}'.")
                # Ensure exit stack is closed
                if server_name in self._active_sessions_exit_stack:
                    stack_to_close = self._active_sessions_exit_stack.pop(server_name)
                    await stack_to_close.aclose()
                    logger.info(f"AsyncExitStack for '{server_name}' closed.")

                # Clean up session, tools, and task reference
                self._active_sessions.pop(server_name, None)
                self._tools_by_server.pop(server_name, None)
                if (
                    self._active_tasks.get(server_name) is task_object
                ):  # Remove only if it's the current task
                    self._active_tasks.pop(server_name, None)

                logger.info(f"Finished cleanup for MCP session '{server_name}'.")

        try:
            # Start the session management in a background task.
            await self._parent_task_group.start(_manage_session_task)
            # If start() returns without error, _manage_session_task has called task_status.started()
            # and registered itself in _active_tasks.
            logger.info(f"MCP session task for '{server_name}' started successfully.")
            return True
        except (
            Exception
        ) as e:  # Catches errors from _manage_session_task BEFORE task_status.started()
            logger.error(
                f"Failed to start MCP session task for '{server_name}' (during startup phase): {e}",
                exc_info=True,
            )
            Console().print(
                f"[red]Error:[/red] Failed to start MCP session for '{server_name}': {e}"
            )
            # _manage_session_task's finally block should handle cleanup of any partial registrations.
            return False

    async def disconnect_server(self, server_name: str) -> bool:
        """Disconnects from a specified MCP server."""
        if server_name not in self._active_tasks:
            Console().print(
                f"[blue]Info:[/blue] MCP server '{server_name}' is not currently connected or already disconnected."
            )
            return False

        task_to_cancel = self._active_tasks.get(server_name)
        if not task_to_cancel:
            return False

        try:
            logger.info(f"Requesting cancellation for MCP task '{server_name}'.")
            task_to_cancel.cancel()

            # Wait for the task to finish its cleanup.
            try:
                await asyncio.wait_for(task_to_cancel, timeout=10.0)
            except asyncio.CancelledError:
                # This is expected - the task was cancelled
                pass
            logger.info(
                f"MCP task '{server_name}' finished after cancellation request."
            )

        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for MCP task '{server_name}' to finish after cancellation. It might still be cleaning up."
            )
        except Exception as e:
            # This might happen if awaiting the cancelled task raises something unexpected.
            logger.error(
                f"Error while waiting for MCP task '{server_name}' to finish after cancellation: {e}",
                exc_info=True,
            )
            # Continue with other cleanup despite this.

        # Remove from active tasks after cleanup attempt
        self._active_tasks.pop(server_name, None)

        # The task's finally block in _manage_session_task handles cleanup of:
        # - _active_sessions_exit_stack[server_name]
        # - _active_sessions[server_name]
        # - _tools_by_server[server_name]

        Console().print(
            f"[green]Success:[/green] Disconnection requested for MCP server '{server_name}'."
        )
        return True

    async def disconnect_all(self):
        """Disconnect all active MCP servers."""
        server_names = list(self._active_tasks.keys())
        for server_name in server_names:
            await self.disconnect_server(server_name)

    def get_active_tools(
        self,
    ) -> List[Tuple[Callable, Dict[str, Any], Type[BaseModel]]]:
        """
        Returns a combined list of tools from all currently active and connected MCP sessions.
        """
        all_tools: List[Tuple[Callable, Dict[str, Any], Type[BaseModel]]] = []
        for server_tools in self._tools_by_server.values():
            all_tools.extend(server_tools)
        logger.debug(
            f"Returning {len(all_tools)} active tools from {len(self._tools_by_server)} servers."
        )
        return all_tools

    @staticmethod
    def _convert_mcp_tool_to_qx_format(
        session: ClientSession, mcp_tool: Any
    ) -> Tuple[Callable, Dict[str, Any], Type[BaseModel]]:
        """
        Converts an MCP tool definition to QX's internal (func, schema, input_model_class) format.
        """
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description
        input_schema = mcp_tool.inputSchema  # This is the JSON schema for parameters

        fields = {}
        for prop_name, prop_details in input_schema.get("properties", {}).items():
            # TODO: Map JSON schema types (prop_details.get("type")) to Python types more accurately if possible.
            # For now, using Any for simplicity.
            field_type = Any
            description = prop_details.get("description", "")

            if prop_name in input_schema.get("required", []):
                # Required field: Use Field(default=..., description=...)
                fields[prop_name] = (
                    field_type,
                    Field(default=..., description=description),
                )
            else:
                # Optional field: Use Field(default=default_value, description=...)
                # Default value can be None or from schema's "default" key.
                default_value_from_schema = prop_details.get(
                    "default"
                )  # Field handles None if key absent
                fields[prop_name] = (
                    field_type,
                    Field(default=default_value_from_schema, description=description),
                )

        # Create the Pydantic model for tool arguments
        ToolInputModel = create_model(
            f"{tool_name.capitalize().replace('_','')}Input",  # Sanitize name for Pydantic
            __base__=BaseModel,  # Ensure it's a Pydantic model
            **fields,  # type: ignore
        )

        # Create a wrapper function that calls the MCP session's tool
        async def wrapper_func(console: Any, args: BaseModel) -> Any:
            # args will be an instance of ToolInputModel
            logger.debug(
                f"Calling MCP tool '{tool_name}' with args: {args.model_dump_json(indent=2)}"
            )
            try:
                # Pass arguments as a dictionary
                result = await session.call_tool(tool_name, args.model_dump())
                logger.debug(f"MCP tool '{tool_name}' raw result: {result}")
                return result.content  # Assuming result has a 'content' attribute
            except Exception as e:
                error_msg = f"Error during MCP tool '{tool_name}' execution: {e}"
                logger.error(error_msg, exc_info=True)
                if console:  # Check if console is provided (it should be)
                    console.print(f"[red]Error:[/red] {error_msg}")
                raise  # Re-raise the exception to be handled by the caller

        wrapper_func.__name__ = tool_name  # Set for better introspection
        # For PydanticAI, the function signature is important.
        # The type hint for 'args' in wrapper_func should ideally be ToolInputModel,
        # but PydanticAI might handle dynamic model binding. Using BaseModel is safer for now.

        # The schema for OpenAI's tool definition (also used by PydanticAI)
        openai_tool_schema = {
            "type": "function",  # OpenAI specific
            "function": {
                "name": tool_name,
                "description": tool_description,
                "parameters": input_schema,  # The raw JSON schema from MCP
            },
        }
        logger.debug(
            f"Converted MCP tool '{tool_name}' to QX format. OpenAI schema: {json.dumps(openai_tool_schema, indent=2)}"
        )
        return wrapper_func, openai_tool_schema, ToolInputModel
