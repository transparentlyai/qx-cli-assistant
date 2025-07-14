"""
Agent invocation plugin for Qx.
Allows agents with delegation permissions to invoke other agents.
"""

import logging
from typing import Optional, Dict
from pydantic import BaseModel, Field

from qx.core.agent_invocation import AgentInvocationService
from rich.console import Console as RichConsole

logger = logging.getLogger(__name__)


def _managed_plugin_print(
    content: str, use_bordered_markdown: bool = False, **kwargs
) -> None:
    """
    Print helper for plugins that uses console manager.
    """
    from qx.cli.console import themed_console
    from qx.cli.quote_bar_component import BorderedMarkdown, get_agent_color
    from qx.core.approval_handler import get_global_agent_context
    from qx.core.console_manager import get_console_manager

    manager = get_console_manager()

    if use_bordered_markdown:
        agent_context = get_global_agent_context()
        if agent_context:
            agent_name = agent_context.get("name")
            agent_color = agent_context.get("color")

            if agent_name:
                from rich.text import Text

                color = get_agent_color(agent_name, agent_color)
                rich_text = Text.from_markup(content)
                bordered_md = BorderedMarkdown(
                    rich_text,
                    border_style=f"dim {color}",
                    background_color="#080808",
                )
                manager.print(bordered_md, console=themed_console, **kwargs)
                return

    manager.print(content, console=themed_console, **kwargs)


class InvokeAgentPluginInput(BaseModel):
    """Input parameters for invoking another agent."""

    agent_name: str = Field(..., description="The name of the agent to invoke")
    prompt: str = Field(
        ..., description="The task or question to delegate to the agent"
    )
    context: Optional[Dict[str, str]] = Field(
        None, description="Optional context variables to pass to the invoked agent"
    )
    timeout: Optional[int] = Field(
        None,
        description="Optional timeout in seconds (defaults to invoked agent's max_execution_time)",
    )


class InvokeAgentPluginOutput(BaseModel):
    """Output from agent invocation."""

    success: bool = Field(..., description="Whether the invocation succeeded")
    response: str = Field(..., description="The agent's response content")
    error: Optional[str] = Field(None, description="Error message if invocation failed")
    agent_name: str = Field(..., description="Name of the invoked agent")


async def invoke_agent_tool(
    console: RichConsole,
    args: InvokeAgentPluginInput,
) -> InvokeAgentPluginOutput:
    """
    Delegate a task to another agent to work in parallel or leverage specialized expertise.

    Use this tool to invoke other agents for faster task completion through parallel
    execution or when you need specialized capabilities. Each invoked agent works
    independently and returns their complete response.

    When to use:
    - Split complex tasks into parallel subtasks for faster completion
    - Need specialized expertise (e.g., security analysis, database optimization)
    - Want to explore multiple approaches simultaneously
    - Have independent tasks that can be processed concurrently
    - Need a fresh perspective without sharing your conversation history

    Arguments:
    - agent_name: Name of the agent to invoke (e.g., "researcher", "security_expert", "code_analyzer")
    - prompt: Clear, detailed description of what you need the agent to do
    - context: Optional key-value pairs to provide additional context
    - timeout: Optional timeout in seconds (uses agent's default if not specified)

    Pro tip: You can invoke multiple agents in a single response to work on different
    parts of a problem simultaneously, significantly speeding up complex tasks.

    Example use cases:
    - Parallel research: Invoke multiple agents to research different aspects of a topic
    - Code review: One agent for security, another for performance, another for best practices
    - Multi-file analysis: Different agents analyzing different parts of a codebase
    - Documentation: One agent writing tests while another writes documentation
    """
    try:
        # Check if multi-agent mode is enabled
        from qx.core.agent_mode_manager import get_agent_mode_manager

        agent_mode_manager = get_agent_mode_manager()
        if agent_mode_manager.is_single:
            error_msg = "Agent invocation is disabled in SINGLE agent mode. Press F2 to switch to MULTI agent mode."
            logger.warning(error_msg)
            _managed_plugin_print(f"[yellow]{error_msg}[/yellow]")

            return InvokeAgentPluginOutput(
                success=False,
                response="",
                error=error_msg,
                agent_name=args.agent_name,
            )
        # Check if current agent has delegation permissions
        # This would typically be enforced at the tool registration level
        # by filtering tools based on agent config

        logger.info(f"Agent invocation requested: {args.agent_name}")

        # Create invocation service
        service = AgentInvocationService()

        # Invoke the target agent
        result = await service.invoke_agent(
            agent_name=args.agent_name,
            prompt=args.prompt,
            context=args.context,
            timeout=args.timeout,
            use_message_history=False,  # Always start fresh
        )

        if result.success:
            logger.info(f"Successfully invoked agent '{args.agent_name}'")
            # Log to console for visibility
            _managed_plugin_print(f"\n[dim]Delegated to {args.agent_name}:[/dim]")
            _managed_plugin_print(result.response, use_bordered_markdown=True)
            _managed_plugin_print(f"[dim]End of {args.agent_name} response[/dim]\n")

            return InvokeAgentPluginOutput(
                success=True,
                response=result.response,
                error=None,
                agent_name=args.agent_name,
            )
        else:
            error_msg = result.error or "Unknown error during agent invocation"
            logger.error(f"Failed to invoke agent '{args.agent_name}': {error_msg}")

            _managed_plugin_print(
                f"[red]Failed to invoke agent '{args.agent_name}': {error_msg}[/red]"
            )

            return InvokeAgentPluginOutput(
                success=False, response="", error=error_msg, agent_name=args.agent_name
            )

    except Exception as e:
        error_msg = f"Exception during agent invocation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(f"[red]{error_msg}[/red]")

        return InvokeAgentPluginOutput(
            success=False, response="", error=error_msg, agent_name=args.agent_name
        )
