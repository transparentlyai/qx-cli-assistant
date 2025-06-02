import argparse
import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import List, Optional

import anyio
from openai.types.chat import ChatCompletionMessageParam

from qx.cli.inline_mode import _handle_llm_interaction, _run_inline_mode
from qx.cli.version import QX_VERSION, display_version_info
from qx.core.config_manager import ConfigManager
from qx.core.constants import DEFAULT_SYNTAX_HIGHLIGHT_THEME
from qx.core.llm import QXLLMAgent
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.logging_config import configure_logging, remove_temp_stream_handler
from qx.core.session_manager import (
    clean_old_sessions,
    load_latest_session,
    load_session_from_path,
    save_session,
)

# Configure logging for the application
logger = logging.getLogger("qx")


async def _async_main(
    initial_prompt: Optional[str] = None,
    exit_after_response: bool = False,
    recover_session_path: Optional[Path] = None,
):
    """
    Asynchronous main function to handle the QX agent logic.
    """
    try:
        configure_logging()
    except Exception as e:
        print(f"Failed to configure logging: {e}")
        traceback.print_exc()
        return

    try:
        async with anyio.create_task_group() as tg:
            config_manager = ConfigManager(None, parent_task_group=tg)
            config_manager.load_configurations()

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

            # Initialize LLM Agent with MCP Manager
            llm_agent: Optional[QXLLMAgent] = await initialize_agent_with_mcp(
                config_manager.mcp_manager
            )

            # Get QX_KEEP_SESSIONS from environment, default to 5 if not set or invalid
            try:
                keep_sessions = int(os.getenv("QX_KEEP_SESSIONS", "5"))
                if keep_sessions < 0:
                    logger.warning(
                        f"QX_KEEP_SESSIONS must be non-negative. Using default of 5 instead of {keep_sessions}."
                    )
                    keep_sessions = 5
            except ValueError:
                logger.warning(
                    "Invalid value for QX_KEEP_SESSIONS. Using default of 5."
                )
                keep_sessions = 5

            # Handle exit after response mode (non-interactive)
            if exit_after_response and initial_prompt:
                current_message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    None,
                    code_theme_to_use,
                    plain_text_output=True,
                )
                if current_message_history:
                    save_session(current_message_history)
                    clean_old_sessions(keep_sessions)
                return  # Return instead of sys.exit() to avoid issues with async context

            current_message_history: Optional[List[ChatCompletionMessageParam]] = None

            # Handle session recovery
            if recover_session_path:
                from rich.console import Console

                if recover_session_path == "LATEST":
                    Console().print("Attempting to recover latest session...")
                    loaded_history = load_latest_session()
                    if loaded_history:
                        current_message_history = loaded_history
                        Console().print("Latest session recovered successfully!")
                    else:
                        Console().print(
                            "[red]No previous sessions found. Starting new session.[/red]"
                        )
                else:
                    Console().print(
                        f"[info]Attempting to recover session from: {recover_session_path}[/info]"
                    )
                    loaded_history = load_session_from_path(Path(recover_session_path))
                    if loaded_history:
                        current_message_history = loaded_history
                        Console().print("[info]Session recovered successfully![/info]")
                    else:
                        Console().print(
                            "[red]Failed to recover session. Starting new session.[/red]"
                        )

            # Handle initial prompt
            if initial_prompt and not exit_after_response:
                from rich.console import Console

                Console().print(f"[bold]Initial Prompt:[/bold] {initial_prompt}")
                current_message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    current_message_history,
                    code_theme_to_use,
                )

            # Run inline interactive mode (only if not in exit-after-response mode)
            if not exit_after_response:
                # Remove the temporary stream handler for inline mode
                remove_temp_stream_handler()

                # Print version info
                from rich.console import Console

                rich_console = Console()
                rich_console.print(
                    f"[dim]QX ver:{QX_VERSION} - {llm_agent.model_name}[/dim]"
                )

                try:
                    # Run inline interactive loop
                    await _run_inline_mode(
                        llm_agent, current_message_history, keep_sessions
                    )
                except KeyboardInterrupt:
                    logger.debug("QX terminated by user (Ctrl+C)")
                    rich_console.print("\nQX terminated by user.")
                except Exception as e:
                    logger.error(f"Error running inline mode: {e}", exc_info=True)
                    rich_console.print(f"[red]App Error:[/red] {e}")
                finally:
                    # Cleanup: disconnect all active MCP servers
                    try:
                        logger.debug("Disconnecting all MCP servers before exit.")
                        await config_manager.mcp_manager.disconnect_all()
                    except Exception as e:
                        logger.error(f"Error during MCP cleanup: {e}", exc_info=True)

                    # Clean up LLM agent resources
                    try:
                        if llm_agent:
                            await llm_agent.cleanup()
                    except Exception as e:
                        logger.error(f"Error during LLM cleanup: {e}", exc_info=True)

    except Exception as e:
        logger.critical(f"Critical error in _async_main: {e}", exc_info=True)
        print(f"Critical error: {e}")
        traceback.print_exc()


def main():
    configure_logging()

    parser = argparse.ArgumentParser(
        description="QX - A terminal-based agentic coding assistant with simplified interface."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show QX version, LLM model, and parameters, then exit.",
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
        type=str,
        nargs="?",
        const="LATEST",
        help="Path to a JSON session file to recover and continue the conversation. If no path is provided, recovers the latest session.",
    )
    parser.add_argument(
        "initial_prompt",
        nargs=argparse.REMAINDER,
        help="Initial prompt for QX. If provided, QX will process this once and then either exit (with -x) or enter interactive mode.",
    )
    args = parser.parse_args()

    if args.version:
        display_version_info()

    initial_prompt_str = " ".join(args.initial_prompt).strip()

    # Handle mutually exclusive arguments
    if args.recover_session and initial_prompt_str:
        from rich.console import Console

        Console().print(
            "[red]Error:[/red] Cannot use --recover-session with an initial prompt. Please choose one."
        )
        sys.exit(1)

    if args.recover_session and args.exit_after_response:
        from rich.console import Console

        Console().print(
            "[red]Error:[/red] Cannot use --recover-session with --exit-after-response. Recovery implies interactive mode."
        )
        sys.exit(1)

    recover_path = (
        args.recover_session
        if args.recover_session == "LATEST"
        else (Path(args.recover_session) if args.recover_session else None)
    )

    try:
        asyncio.run(
            _async_main(
                initial_prompt=initial_prompt_str if initial_prompt_str else None,
                exit_after_response=args.exit_after_response,
                recover_session_path=recover_path,
            )
        )

        # If exit_after_response is True, we should exit here
        if args.exit_after_response:
            sys.exit(0)

    except KeyboardInterrupt:
        from rich.console import Console

        Console().print("\nQX terminated by user.")
        sys.exit(0)
    except Exception as e:
        fallback_logger = logging.getLogger("qx.critical")
        fallback_logger.critical(f"Critical error running QX: {e}", exc_info=True)
        from rich.console import Console

        Console().print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
