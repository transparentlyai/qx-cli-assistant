import argparse
import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import List, Optional

import anyio
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)

from qx.cli.inline_mode import _handle_llm_interaction, _run_inline_mode
from qx.cli.session_selector import select_session
from qx.cli.version import QX_VERSION, display_version_info
from qx.core.config_manager import ConfigManager
from qx.core.constants import DEFAULT_SYNTAX_HIGHLIGHT_THEME
from qx.core.llm import QXLLMAgent, load_and_format_system_prompt
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.agent_manager import get_agent_manager
from qx.core.logging_config import configure_logging, remove_temp_stream_handler
from qx.core.session_manager import (
    clean_old_sessions,
    load_session_from_path,
    save_session,
)
from qx.core.state_manager import details_manager

# Configure logging for the application
logger = logging.getLogger("qx")


async def _async_main(
    initial_prompt: Optional[str] = None,
    exit_after_response: bool = False,
    recover_session: bool = False,
):
    """
    Asynchronous main function to handle the Qx agent logic.
    """
    agent_manager = None
    try:
        async with anyio.create_task_group() as tg:
            config_manager = ConfigManager(None, parent_task_group=tg)
            try:
                config_manager.load_configurations()
            except SystemExit as e:
                # Handle clean exit for security errors
                return e.code

            # Initialize the DetailsManager
            await details_manager.is_active()  # This initializes the singleton

            # Configure logging after config is loaded so QX_LOG_LEVEL is available
            configure_logging()

            logger.debug("Using Textual interface.")

            syntax_theme_from_env = os.getenv("QX_SYNTAX_HIGHLIGHT_THEME")
            code_theme_to_use = (
                syntax_theme_from_env
                if syntax_theme_from_env
                else DEFAULT_SYNTAX_HIGHLIGHT_THEME
            )
            logger.debug(
                f"Using syntax highlighting theme for Markdown code blocks: {code_theme_to_use}"
            )

            # Initialize Agent Manager and load default agent
            agent_manager = get_agent_manager()

            # Check team mode to determine which agent to load at startup
            from qx.core.team_mode_manager import get_team_mode_manager
            team_mode_manager = get_team_mode_manager()
            
            # Reset team manager to ensure teams are loaded from persistent storage
            from qx.core.team_manager import reset_team_manager
            reset_team_manager()
            
            # Determine default agent based on team mode state
            if team_mode_manager.is_team_mode_enabled():
                default_agent_name = os.environ.get("QX_DEFAULT_AGENT", "qx-director")
            else:
                default_agent_name = os.environ.get("QX_DEFAULT_AGENT", "qx")
            try:
                default_agent_result = await agent_manager.load_agent(
                    default_agent_name,
                    context={
                        "user_context": os.environ.get("QX_USER_CONTEXT", ""),
                        "project_context": os.environ.get("QX_PROJECT_CONTEXT", ""),
                        "project_files": os.environ.get("QX_PROJECT_FILES", ""),
                        "ignore_paths": "",  # Will be filled by prompt formatting
                    },
                    cwd=os.getcwd(),
                )

                # Initialize LLM Agent with loaded agent configuration
                if (
                    default_agent_result.success
                    and default_agent_result.agent is not None
                ):
                    logger.info(
                        f"Loaded agent '{default_agent_name}' from {default_agent_result.source_path}"
                    )
                    llm_agent: Optional[QXLLMAgent] = await initialize_agent_with_mcp(
                        config_manager.mcp_manager,
                        agent_config=default_agent_result.agent,
                    )

                    # Set the current agent session in the agent manager
                    # This is needed so /agents info works correctly
                    # Use the internal method to avoid deadlock issues
                    agent_manager._set_current_agent_session(
                        default_agent_name, default_agent_result.agent
                    )

                    # Register the active LLM agent so it can be updated during agent switching
                    agent_manager.set_active_llm_agent(llm_agent)
                else:
                    raise Exception(
                        f"Failed to load agent '{default_agent_name}': {default_agent_result.error}"
                    )

            except Exception as e:
                logger.warning(f"Agent-based initialization failed: {e}")
                logger.info("Falling back to legacy system prompt loading")
                # Fallback to legacy initialization
                fallback_llm_agent: Optional[
                    QXLLMAgent
                ] = await initialize_agent_with_mcp(config_manager.mcp_manager)
                llm_agent = fallback_llm_agent

            # Get QX_KEEP_SESSIONS from environment, default to 20 if not set or invalid
            try:
                keep_sessions = int(os.getenv("QX_KEEP_SESSIONS", "20"))
                if keep_sessions < 0:
                    logger.warning(
                        f"QX_KEEP_SESSIONS must be non-negative. Using default of 20 instead of {keep_sessions}."
                    )
                    keep_sessions = 20
            except ValueError:
                logger.warning(
                    "Invalid value for QX_KEEP_SESSIONS. Using default of 20."
                )
                keep_sessions = 20

            # Handle exit after response mode (non-interactive)
            if exit_after_response and initial_prompt:
                if llm_agent is None:
                    logger.error("LLM agent initialization failed")
                    return
                message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    None,
                    code_theme_to_use,
                    plain_text_output=True,
                    config_manager=config_manager,
                )
                if message_history:
                    save_session(message_history)
                    clean_old_sessions(keep_sessions)
                return  # Return instead of sys.exit() to avoid issues with async context

            current_message_history: Optional[List[ChatCompletionMessageParam]] = None

            # Handle session recovery
            if recover_session:
                from qx.cli.theme import themed_console

                recover_session_path = select_session()

                if recover_session_path:
                    themed_console.print(
                        f"[info]Attempting to recover session from: {recover_session_path}[/]"
                    )
                    loaded_history = load_session_from_path(Path(recover_session_path))
                    if loaded_history:
                        # Use agent-based system prompt if available, fallback to legacy
                        current_agent = await agent_manager.get_current_agent()
                        if current_agent:
                            system_prompt = load_and_format_system_prompt(current_agent)
                        else:
                            system_prompt = load_and_format_system_prompt()

                        current_message_history = [
                            ChatCompletionSystemMessageParam(
                                role="system", content=system_prompt
                            )
                        ] + loaded_history
                        themed_console.print(
                            "[success]Session recovered successfully![/]"
                        )

                        # Automatically ask for a summary
                        if llm_agent:
                            current_message_history = await _handle_llm_interaction(
                                llm_agent,
                                "list a summary of each iteraction we had so far - just the list, with a title 'So far in this session' and a separator at the end of the list - **ONLY the list,title and separator, no other text**",
                                current_message_history,
                                code_theme_to_use,
                                config_manager=config_manager,
                            )

                    else:
                        themed_console.print(
                            "[error]Failed to recover session. Starting new session.[/]"
                        )
                else:
                    themed_console.print(
                        "[error]No session selected. Starting new session.[/]"
                    )

            # Handle initial prompt
            if initial_prompt and not exit_after_response:
                from qx.cli.theme import themed_console

                themed_console.print(
                    f"[text.important]Initial Prompt:[/] {initial_prompt}"
                )
                if llm_agent is None:
                    logger.error("LLM agent initialization failed")
                    return
                current_message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    current_message_history,
                    code_theme_to_use,
                    config_manager=config_manager,
                )

            # Run inline interactive mode (only if not in exit-after-response mode)
            if not exit_after_response:
                # Remove the temporary stream handler for inline mode
                remove_temp_stream_handler()

                if llm_agent is None:
                    logger.error("LLM agent initialization failed")
                    return

                # Print version info
                from qx.cli.theme import themed_console

                themed_console.print(
                    f"\n[dim]Qx ver:[info]{QX_VERSION}[/] | [dim]model:[/][info]{os.path.basename(llm_agent.model_name)}[/] | [dim]cwd:[/][info]{os.getcwd()}[/]"
                )

                try:
                    # Run inline interactive loop
                    await _run_inline_mode(
                        llm_agent,
                        current_message_history,
                        keep_sessions,
                        config_manager,
                    )
                except KeyboardInterrupt:
                    logger.debug("Qx terminated by user (Ctrl+C)")
                    themed_console.print("\nQx terminated by user.")
                except Exception as e:
                    logger.error(f"Error running inline mode: {e}", exc_info=True)
                    themed_console.print(f"[error]App Error:[/] {e}")
                finally:
                    # Cleanup: disconnect all active MCP servers
                    try:
                        logger.debug("Disconnecting all MCP servers before exit.")
                        await config_manager.mcp_manager.disconnect_all()
                    except Exception as e:
                        logger.error(f"Error during MCP cleanup: {e}", exc_info=True)

                    # Clean up HTTP client resources
                    try:
                        from qx.core.http_client_manager import http_client_manager
                        logger.debug("Cleaning up HTTP client before exit.")
                        await http_client_manager.cleanup()
                    except Exception as e:
                        logger.error(f"Error during HTTP client cleanup: {e}", exc_info=True)

                    # Clean up LLM agent resources
                    try:
                        if llm_agent:
                            await llm_agent.cleanup()
                    except Exception as e:
                        logger.error(f"Error during LLM cleanup: {e}", exc_info=True)

                    # Clean up agent manager resources
                    try:
                        if agent_manager:
                            await agent_manager.cleanup()
                    except Exception as e:
                        logger.error(
                            f"Error during agent manager cleanup: {e}", exc_info=True
                        )

    except Exception as e:
        logger.critical(f"Critical error in _async_main: {e}", exc_info=True)
        print(f"Critical error: {e}")
        traceback.print_exc()


def main():
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Qx - A terminal-based agentic coding assistant with simplified interface."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show Qx version, LLM model, and parameters, then exit.",
    )
    parser.add_argument(
        "-x",
        "--exit-after-response",
        action="store_true",
        help="Exit immediately after responding to an initial prompt.",
    )
    parser.add_argument(
        "-r",
        "--recover-session",
        action="store_true",
        help="Shows a list of previous sessions to recover and continue the conversation.",
    )
    parser.add_argument(
        "initial_prompt",
        nargs=argparse.REMAINDER,
        help="Initial prompt for QX. If provided, Qx will process this once and then either exit (with -x) or enter interactive mode.",
    )
    args = parser.parse_args()

    if args.version:
        display_version_info()

    initial_prompt_str = " ".join(args.initial_prompt).strip()

    # Handle mutually exclusive arguments
    if args.recover_session and initial_prompt_str:
        from qx.cli.theme import themed_console

        themed_console.print(
            "[error]Error:[/] Cannot use --recover-session with an initial prompt. Please choose one."
        )
        sys.exit(1)

    if args.recover_session and args.exit_after_response:
        from qx.cli.theme import themed_console

        themed_console.print(
            "[error]Error:[/] Cannot use --recover-session with --exit-after-response. Recovery implies interactive mode."
        )
        sys.exit(1)

    try:
        asyncio.run(
            _async_main(
                initial_prompt=initial_prompt_str if initial_prompt_str else None,
                exit_after_response=args.exit_after_response,
                recover_session=args.recover_session,
            )
        )

        # If exit_after_response is True, we should exit here
        if args.exit_after_response:
            sys.exit(0)

    except KeyboardInterrupt:
        from qx.cli.theme import themed_console

        themed_console.print("\nQx terminated by user.")
        sys.exit(0)
    except Exception as e:
        fallback_logger = logging.getLogger("qx.critical")
        fallback_logger.critical(f"Critical error running QX: {e}", exc_info=True)
        from qx.cli.theme import themed_console

        themed_console.print(f"[critical]Critical error running QX:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
