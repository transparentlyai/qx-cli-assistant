import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt from the markdown file and formats it with
    environment variables and runtime information.
    """
    try:
        # Adjust path since we're now in a subdirectory
        current_dir = Path(__file__).parent
        prompt_path = current_dir.parent.parent / "prompts" / "system-prompt.md"

        if not prompt_path.exists():
            logger.error(f"System prompt file not found at {prompt_path}")
            return "You are a helpful AI assistant."

        template = prompt_path.read_text(encoding="utf-8")
        user_context = os.environ.get("QX_USER_CONTEXT", "")
        project_context = os.environ.get("QX_PROJECT_CONTEXT", "")
        project_files = os.environ.get("QX_PROJECT_FILES", "")

        # Read .gitignore from the runtime CWD
        try:
            # Get the current working directory where the qx command is run
            runtime_cwd = Path(os.getcwd())
            gitignore_path = runtime_cwd / ".gitignore"
            if gitignore_path.exists():
                ignore_paths = gitignore_path.read_text(encoding="utf-8")
            else:
                ignore_paths = "# No .gitignore file found in the current directory."
        except Exception as e:
            logger.warning(f"Could not read .gitignore file: {e}")
            ignore_paths = "# Error reading .gitignore file."

        formatted_prompt = template.replace("{user_context}", user_context)
        formatted_prompt = formatted_prompt.replace(
            "{project_context}", project_context
        )
        formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
        formatted_prompt = formatted_prompt.replace("{ignore_paths}", ignore_paths)

        logger.debug(f"Final System Prompt:\n{formatted_prompt}")

        return formatted_prompt
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."
