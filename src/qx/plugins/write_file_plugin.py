import difflib
import logging
import os
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from rich.console import Console as RichConsole  # For type hint and direct use
from rich.syntax import Syntax
from rich.text import Text

from qx.core.context import QXToolDependencies
from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)

# Constants for preview
MAX_PREVIEW_LINES = 30
HEAD_LINES = 12
TAIL_LINES = 12


# --- Duplicated from src/qx/tools/file_operations_base.py ---
def is_path_allowed(
    resolved_path: Path, project_root: Optional[Path], user_home: Path
) -> bool:
    path_to_check = resolved_path.resolve()
    if project_root:
        project_root_abs = project_root.resolve()
        if (
            path_to_check == project_root_abs
            or project_root_abs in path_to_check.parents
        ):
            return True
        dot_q_path = (project_root_abs / ".Q").resolve()
        if path_to_check == dot_q_path or dot_q_path in path_to_check.parents:
            return True
    user_home_abs = user_home.resolve()
    if path_to_check == user_home_abs or user_home_abs in path_to_check.parents:
        return True
    return False


# --- End of duplicated is_path_allowed ---


# --- Copied and adapted from src/qx/tools/write_file.py (write_file_impl) ---
def _write_file_core_logic(path_str: str, content: str) -> Optional[str]:
    """
    Core logic to write content to a file. Does not handle approval.
    Returns None if successful, or an error message string.
    """
    try:
        expanded_path_str = os.path.expanduser(path_str)
        current_working_dir = Path.cwd()
        project_root = _find_project_root(str(current_working_dir))
        absolute_path = Path(expanded_path_str)
        if not absolute_path.is_absolute():
            absolute_path = current_working_dir.joinpath(expanded_path_str).resolve()
        else:
            absolute_path = absolute_path.resolve()

        # is_path_allowed check is done before calling this core logic in the plugin
        # but can be kept here as a safeguard if this function were ever called directly.
        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            logger.error(f"Write access denied by policy (core logic): {absolute_path}")
            return f"Error: Access denied by policy for path: {absolute_path}"

        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote to file: {absolute_path}")
        return None
    except PermissionError:
        logger.error(f"Permission denied writing to file: {path_str}")
        return f"Error: Permission denied writing to file: {path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, cannot write: {path_str}")
        return f"Error: Path is a directory, cannot write: {path_str}"
    except Exception as e:
        logger.error(f"Error writing to file '{path_str}': {e}", exc_info=True)
        return f"Error writing to file '{path_str}': {e}"


# --- End of _write_file_core_logic ---


# --- Adapted from ApprovalManager._get_file_preview_renderables for write_file ---
def _generate_write_preview(
    file_path_str: str,
    new_content: str,
    syntax_theme: str = "vim",  # Default theme
) -> Union[Text, Syntax, None]:
    """Generates a Rich renderable for file write preview (diff or new content)."""
    file_path = Path(os.path.expanduser(file_path_str))
    file_ext = file_path.suffix.lstrip(".").lower()
    lexer_name = file_ext or "text"
    try:
        get_lexer_by_name(lexer_name)
    except ClassNotFound:
        lexer_name = "text"

    if file_path.exists() and file_path.is_file():
        try:
            old_content = file_path.read_text(encoding="utf-8")
            if old_content == new_content:
                return Text(
                    "[bold yellow]No changes detected - file content is identical.[/bold yellow]"
                )

            old_lines = old_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            diff_lines = list(
                difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"Current: {file_path_str}",
                    tofile=f"New: {file_path_str}",
                    lineterm="\n",
                    n=3,
                )
            )
            if diff_lines:
                return Syntax(
                    "".join(diff_lines),
                    "diff",
                    theme="vim",
                    line_numbers=False,
                    word_wrap=True,
                )
            return Text(
                "[bold yellow]No textual changes detected in diff (content might be identical after normalization).[/bold yellow]"
            )
        except Exception as e:
            logger.error(
                f"Error generating diff for {file_path_str}: {e}", exc_info=True
            )
            # Fallback to showing new content if diff fails

    # Show new content if file doesn't exist or diff failed
    all_lines = new_content.splitlines()
    line_count = len(all_lines)
    bg_color = "default" if syntax_theme not in ["rrt", "dimmed_monokai"] else None

    if line_count > MAX_PREVIEW_LINES:
        head_str = "\n".join(all_lines[:HEAD_LINES])
        tail_str = "\n".join(all_lines[-TAIL_LINES:])
        display_content_str = (
            f"{head_str}\n\n"
            f"[dim i]... {line_count - HEAD_LINES - TAIL_LINES} more lines ...[/dim i]\n\n"
            f"{tail_str}"
        )
        # For truncated content, Syntax might not be ideal if it adds its own chrome.
        # A simple Text object might be better, or a custom renderable.
        # For now, let's use Syntax but be mindful of its rendering of partial content.
        # The original ApprovalManager used Syntax for this.
        return Syntax(
            display_content_str,
            lexer_name,
            theme=syntax_theme,
            line_numbers=True,
            word_wrap=True,
            background_color=bg_color,
        )
    else:
        return Syntax(
            new_content,
            lexer_name,
            theme=syntax_theme,
            line_numbers=True,
            word_wrap=True,
            background_color=bg_color,
        )


# --- End of _generate_write_preview ---


class WriteFilePluginInput(BaseModel):
    """Input model for the WriteFilePluginTool."""

    path: str = Field(
        ..., description="Path to the file. Parent dirs created if needed."
    )
    content: str = Field(..., description="Raw content to write.")


class WriteFilePluginOutput(BaseModel):
    """Output model for the WriteFilePluginTool."""

    path: str = Field(
        description="The (expanded and possibly modified) path of the file."
    )
    success: bool = Field(description="True if write was successful.")
    message: str = Field(description="Result message or error.")


def write_file_tool(
    ctx: RunContext[QXToolDependencies], args: WriteFilePluginInput
) -> WriteFilePluginOutput:
    """
    Tool to write content to a file.
    Allows path modification by user.
    Restricted by policy to project or user's home directory.
    """
    console = ctx.deps.console
    original_path_arg = args.path
    path_to_consider = os.path.expanduser(
        original_path_arg
    )  # Start with this for checks and prompts

    # Preliminary security check
    current_working_dir = Path.cwd()
    project_root = _find_project_root(str(current_working_dir))
    absolute_path_to_evaluate = Path(path_to_consider)
    if not absolute_path_to_evaluate.is_absolute():
        absolute_path_to_evaluate = current_working_dir.joinpath(
            path_to_consider
        ).resolve()
    else:
        absolute_path_to_evaluate = absolute_path_to_evaluate.resolve()

    if not is_path_allowed(absolute_path_to_evaluate, project_root, USER_HOME_DIR):
        err_msg = f"Error: Access denied by policy for path: {path_to_consider}"
        logger.error(
            f"Write access denied by policy (plugin pre-check) for path: {path_to_consider}"
        )
        return WriteFilePluginOutput(
            path=path_to_consider, success=False, message=err_msg
        )

    # Generate preview
    # TODO: Get syntax_theme from config or context if made configurable
    preview_renderable = _generate_write_preview(
        path_to_consider, args.content, syntax_theme="vim"
    )

    prompt_msg = f"Allow QX to write to file: '{path_to_consider}'?"
    decision_status, final_value = request_confirmation(
        prompt_message=prompt_msg,
        console=console,
        content_to_display=preview_renderable,
        allow_modify=True,  # Allow path modification
        current_value_for_modification=path_to_consider,
    )

    path_to_write: str
    if decision_status == "modified" and final_value is not None:
        path_to_write = final_value
        logger.info(
            f"Write path modified by user from '{path_to_consider}' to '{path_to_write}'."
        )
        # Re-check is_path_allowed for the new path
        absolute_modified_path = Path(os.path.expanduser(path_to_write))
        if not absolute_modified_path.is_absolute():
            absolute_modified_path = current_working_dir.joinpath(
                path_to_write
            ).resolve()
        else:
            absolute_modified_path = absolute_modified_path.resolve()

        if not is_path_allowed(absolute_modified_path, project_root, USER_HOME_DIR):
            err_msg = (
                f"Error: Access denied by policy for modified path: {path_to_write}"
            )
            logger.error(f"Write access denied for modified path: {path_to_write}")
            return WriteFilePluginOutput(
                path=path_to_write, success=False, message=err_msg
            )
    elif decision_status in ["approved", "session_approved"]:  # MODIFIED LINE
        path_to_write = path_to_consider
    else:  # denied or cancelled
        error_message = (
            f"Write operation for '{path_to_consider}' was {decision_status} by user."
        )
        logger.warning(error_message)
        # request_confirmation already prints a message for denied/cancelled
        return WriteFilePluginOutput(
            path=path_to_consider, success=False, message=error_message
        )

    # Proceed to write
    error_from_impl = _write_file_core_logic(path_to_write, args.content)

    if error_from_impl:
        return WriteFilePluginOutput(
            path=path_to_write, success=False, message=error_from_impl
        )
    else:
        # If session_approved, request_confirmation already printed a success message.
        # If just "approved", it might be good to confirm the write.
        # However, the original logic didn't print a specific success message here, relying on subsequent tool output.
        # For now, keeping it consistent. A success message is in the return object.
        return WriteFilePluginOutput(
            path=path_to_write,
            success=True,
            message=f"Successfully wrote to {path_to_write}",
        )


if __name__ == "__main__":
    import shutil

    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    test_deps = QXToolDependencies(console=test_console)

    class DummyRunContext(RunContext[QXToolDependencies]):
        def __init__(self, deps: QXToolDependencies):
            super().__init__(deps=deps, usage=None)  # type: ignore

    dummy_ctx = DummyRunContext(deps=test_deps)

    test_base = Path("./tmp_write_plugin_test_ctx").resolve()
    if test_base.exists():
        shutil.rmtree(test_base)
    test_base.mkdir(exist_ok=True)

    test_project = test_base / "test_project_write_ctx"
    test_project.mkdir(exist_ok=True)
    (test_project / ".Q").mkdir(exist_ok=True)

    original_cwd = Path.cwd()
    os.chdir(test_project)

    test_console.rule("Testing write_file_tool plugin with RunContext")

    # Test 1: Write new file in project (user approves)
    test_console.print("\n[bold]Test 1: Write new project file (approve path)[/]")
    input1 = WriteFilePluginInput(
        path="new_project_file.txt", content="Hello from write plugin!"
    )
    test_console.print("Please respond 'y' to the prompt.")
    output1 = write_file_tool(dummy_ctx, input1)
    test_console.print(f"Output 1: {output1}")
    if output1.success:
        assert (
            test_project / "new_project_file.txt"
        ).read_text() == "Hello from write plugin!"

    # Test 2: Modify existing file in project (user approves diff)
    existing_file = test_project / "existing_project_file.txt"
    existing_file.write_text("Old line 1\nOld line 2")
    test_console.print("\n[bold]Test 2: Modify existing project file (approve diff)[/]")
    input2 = WriteFilePluginInput(
        path="existing_project_file.txt", content="New line 1\nOld line 2\nNew line 3"
    )
    test_console.print("Please respond 'y' to the prompt.")
    output2 = write_file_tool(dummy_ctx, input2)
    test_console.print(f"Output 2: {output2}")
    if output2.success:
        assert (
            test_project / "existing_project_file.txt"
        ).read_text() == "New line 1\nOld line 2\nNew line 3"

    # Test 3: Write to home, path modification (user modifies path)
    home_test_file_original_name = "qx_write_plugin_home_original.txt"
    home_test_file_modified_name = "qx_write_plugin_home_MODIFIED.txt"

    os.chdir(
        original_cwd
    )  # Change CWD to ensure tilde path is outside project for confirmation
    test_console.print(
        f"\n[bold]Test 3: Write to home, user modifies path from ~/{home_test_file_original_name} to ~/{home_test_file_modified_name}[/]"
    )
    input3 = WriteFilePluginInput(
        path=f"~/{home_test_file_original_name}", content="Content for modified path."
    )
    test_console.print(
        f"At the prompt: respond 'm', then enter '~/{home_test_file_modified_name}', then 'y' (if a second confirm appears) or just enter."
    )
    output3 = write_file_tool(dummy_ctx, input3)
    test_console.print(f"Output 3: {output3}")
    if output3.success:
        assert (USER_HOME_DIR / home_test_file_modified_name).exists()
        assert (
            USER_HOME_DIR / home_test_file_modified_name
        ).read_text() == "Content for modified path."
        (USER_HOME_DIR / home_test_file_modified_name).unlink(missing_ok=True)
    (USER_HOME_DIR / home_test_file_original_name).unlink(
        missing_ok=True
    )  # cleanup original if created by mistake

    # Test 4: Denied by policy
    test_console.print("\n[bold]Test 4: Write to /etc/somefile (policy denial)[/]")
    input4 = WriteFilePluginInput(
        path="/etc/this_should_fail.txt", content="Forbidden content"
    )
    output4 = write_file_tool(dummy_ctx, input4)  # No prompt expected, direct denial
    test_console.print(f"Output 4: {output4}")
    assert not output4.success and "Access denied by policy" in output4.message

    # Test 5: User denies
    os.chdir(test_project)  # Back to project dir
    test_console.print("\n[bold]Test 5: User denies write to project file[/]")
    input5 = WriteFilePluginInput(
        path="user_denies_this.txt", content="This won't be written."
    )
    test_console.print("Please respond 'n' to the prompt.")
    output5 = write_file_tool(dummy_ctx, input5)
    test_console.print(f"Output 5: {output5}")
    assert not output5.success and "denied by user" in output5.message
    assert not (test_project / "user_denies_this.txt").exists()

    os.chdir(original_cwd)
    shutil.rmtree(test_base)
    test_console.print("\nWrite_file_plugin (with context) tests finished.")
