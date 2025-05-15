# Project QX Log

## Sprint 1: Project Setup & Core CLI Structure (Done)

**Date:** 2024-07-15

**Objective:** Initialize the project, set up the basic directory structure, and create the main entry point for the CLI.

**Tasks Completed:**

1.  **Project Initialization:**
    *   Created `pyproject.toml` with basic metadata and dependencies (`pydantic-ai`, `python-dotenv`, `rich`, `prompt-toolkit`).
    *   Initialized `uv` environment.
    *   Created `.gitignore`.
2.  **Directory Structure:**
    *   `src/qx/main.py`: Main CLI entry point.
    *   `src/qx/core/`: For core logic (LLM interaction, config).
    *   `src/qx/cli/`: For CLI specific modules (e.g., custom prompt).
    *   `src/qx/tools/`: For agent tools.
    *   `.Q/`: For project-specific directives, logs, and documentation.
        *   `.Q/project.md`: Project QX Directives.
        *   `.Q/projectlog.md`: This file.
        *   `.Q/documentation/`: For external library documentation.
3.  **`src/qx/main.py`:**
    *   Initial `main()` function.
    *   Placeholder for `async_main()` to handle core logic.
    *   Basic Rich console output.
    *   Environment variable loading for `QX_MODEL_NAME`, `QX_VERTEX_PROJECT_ID`, `QX_VERTEX_LOCATION`.
    *   Initial checks for these environment variables.
4.  **`src/qx/cli/qprompt.py`:**
    *   Created `get_user_input()` function using `prompt_toolkit.PromptSession` for asynchronous input.
    *   Basic loop in `main.py` to get user input and echo it.
    *   Exit condition (`exit`, `quit`).

**Next Steps:**

*   Implement LLM initialization and basic querying.
*   Refine error handling.

---

## Sprint 2: LLM Integration & Async Main Loop (Done)

**Date:** 2024-07-15

**Objective:** Integrate Pydantic-AI for LLM interaction and implement the main asynchronous loop for the agent.

**Tasks Completed:**

1.  **`src/qx/core/llm.py`:**
    *   Created `initialize_llm_agent()`:
        *   Takes `model_name`, `project_id`, `location` as parameters.
        *   Initializes `pydantic_ai.Agent`.
        *   Handles potential exceptions during agent initialization.
    *   Created `query_llm()`:
        *   Takes `agent` and `user_input` as parameters.
        *   Calls `agent.run()` asynchronously.
        *   Returns the LLM response output.
        *   Handles potential exceptions during `agent.run()`.
2.  **`src/qx/main.py` Updates:**
    *   Renamed `main()` to `_async_main()` and made it asynchronous.
    *   Created a new synchronous `main()` function that runs `_async_main()` using `asyncio.run()`.
    *   Integrated `initialize_llm_agent()`:
        *   Reads `QX_MODEL_NAME`, `QX_VERTEX_PROJECT_ID`, `QX_VERTEX_LOCATION` from environment variables.
        *   Passes these to `initialize_llm_agent()`.
    *   Integrated `query_llm()` into the main loop:
        *   Passes the initialized agent and user input.
        *   Prints the LLM response or error messages using Rich console.
    *   Improved error handling for agent initialization and querying.
    *   Added console messages for agent status (initialized, thinking).
3.  **Environment Variable Handling:**
    *   Ensured `QX_MODEL_NAME` is mandatory.
    *   `QX_VERTEX_PROJECT_ID` and `QX_VERTEX_LOCATION` are optional, with warnings if not set (PydanticAI might use gcloud defaults).
4.  **`.env` file:**
    *   Created a `.env` file with placeholder/example values for `QX_MODEL_NAME`, `QX_VERTEX_PROJECT_ID`, `QX_VERTEX_LOCATION`.
    *   Added `.env` to `.gitignore`.

**Next Steps:**

*   Implement system prompt loading.
*   Develop file operation tools (read, write).

---

## Sprint 3: System Prompt Loading (Done)

**Date:** 2024-07-16

**Objective:** Implement dynamic loading of the system prompt from `src/qx/prompts/system-prompt.md`.

**Tasks Completed:**

1.  **Created `src/qx/prompts/system-prompt.md`:**
    *   Defined the initial multi-part system prompt structure as per the agent's persona and mission.
    *   Included placeholders for dynamic content like `{user_context}`, `{project_context}`, and `{project_files}`.
2.  **Modified `src/qx/core/llm.py`:**
    *   Created `load_system_prompt()` function:
        *   Takes `prompt_path` as an argument.
        *   Reads the content of the markdown file.
        *   Returns the prompt string or a default error message if the file is not found or unreadable.
    *   Updated `initialize_llm_agent()`:
        *   Calls `load_system_prompt()` to get the system prompt content.
        *   **Decision:** For now, the dynamic placeholders (`{user_context}`, etc.) will be passed as empty strings. Actual context loading will be a separate task.
        *   Formats the loaded prompt string with these empty placeholders.
        *   Passes the formatted system prompt to `pydantic_ai.Agent(system_prompt=...)`.
        *   Handles cases where the system prompt fails to load, allowing the agent to initialize with PydanticAI's default system prompt if any, or none.
3.  **Error Handling:**
    *   Added error messages if `system-prompt.md` cannot be loaded, printing to the console. The agent will still attempt to initialize.

**Next Steps:**

*   Implement the `read_file` tool.
*   Implement the `write_file` tool.
*   Begin work on loading actual dynamic context for the system prompt placeholders.

---

## Sprint 4: Implement `read_file` Tool (Done)

**Date:** 2024-07-16

**Objective:** Create and integrate the `read_file` tool for the QX agent.

**Tasks Completed:**

1.  **Created `src/qx/tools/read_file.py`:**
    *   Defined the `read_file(path: str) -> str | None` function.
    *   The function takes a relative or absolute file path as a string.
    *   It resolves the path to an absolute path.
    *   **Security Consideration:** For now, it does not implement strict path restrictions (e.g., jailing to project directory). This will be addressed later. A placeholder comment for security review is added.
    *   Reads the file content using `utf-8` encoding.
    *   Returns the file content as a string.
    *   Includes error handling for `FileNotFoundError` and `IOError`, printing an error message and returning `None` in case of an error.
2.  **Tool Integration (`src/qx/core/llm.py`):**
    *   Imported `read_file` from `..tools.read_file`.
    *   Registered `read_file` in the `tools` list during `Agent` initialization: `Agent(..., tools=[read_file])`.
    *   Added a console message confirming successful agent initialization with the tool.

**Next Steps:**

*   Implement the `write_file` tool.
*   Address path restriction security for `read_file`.
*   Implement dynamic context loading for system prompt.

---

## Sprint 5: Implement `write_file` Tool (Done)

**Date:** 2024-07-17

**Objective:** Create and integrate the `write_file` tool for the QX agent.

**Tasks Completed:**

1.  **Created `src/qx/tools/write_file.py`:**
    *   Defined the `write_file(path: str, content: str) -> bool` function.
    *   Takes a relative or absolute file path string and content string.
    *   Resolves the path to an absolute path.
    *   **Security Consideration:** Added a placeholder comment for security review regarding path restrictions (jailing).
    *   Creates parent directories if they don't exist using `os.makedirs(..., exist_ok=True)`.
    *   Writes the content to the file using `utf-8` encoding.
    *   Returns `True` on successful write.
    *   Includes error handling for `IOError` and other `OSError` exceptions, printing an error message and returning `False`.
2.  **Tool Integration (`src/qx/core/llm.py`):**
    *   Imported `write_file` from `..tools.write_file`.
    *   Registered `write_file` in the `tools` list during `Agent` initialization, alongside `read_file`: `Agent(..., tools=[read_file, write_file])`.
    *   Updated the console message to reflect both tools are being initialized.
3.  **Updated `src/qx/tools/__init__.py` and `src/qx/core/__init__.py`:**
    *   Ensured `__init__.py` files exist in `tools` and `core` directories to mark them as packages.

**Next Steps:**

*   Implement path restriction security for `read_file` and `write_file`.
*   Implement dynamic context loading for system prompt placeholders (`{user_context}`, `{project_context}`, `{project_files}`).

---

## Sprint 6: Implement Dynamic Context Loading for System Prompt (Done)

**Date:** 2024-07-17

**Objective:** Load actual dynamic context for `{user_context}`, `{project_context}`, and `{project_files}` placeholders in the system prompt.

**Tasks Completed:**

1.  **Created `src/qx/core/config_manager.py`:**
    *   Defined `USER_HOME_DIR = Path.home().resolve()`.
    *   **`_find_project_root(cwd_str: str) -> Path | None` function:**
        *   Takes current working directory string.
        *   Searches upwards for `.Q` or `.git` directory to identify project root.
        *   Stops search at `USER_HOME_DIR` or its parent to prevent scanning the entire filesystem.
        *   Returns the `Path` object of the project root or `None`.
    *   **`load_runtime_configurations()` function:**
        *   **User Context (`QX_USER_CONTEXT`):**
            *   Reads from `~/.config/q/user.md`.
            *   Sets `QX_USER_CONTEXT` environment variable. Defaults to empty string if file not found.
        *   **Project Root Determination:** Calls `_find_project_root(str(Path.cwd()))`.
        *   **Project Context (`QX_PROJECT_CONTEXT`):**
            *   If project root is found, reads from `project_root/.Q/project.md`.
            *   Sets `QX_PROJECT_CONTEXT` environment variable. Defaults to empty string.
        *   **Project Files (`QX_PROJECT_FILES`):**
            *   If project root is found AND `Path.cwd()` is NOT `USER_HOME_DIR`:
                *   Constructs a `tree -a` command.
                *   **Ignore Patterns:**
                    *   Starts with `DEFAULT_TREE_IGNORE_PATTERNS` (defined in `src/qx/core/constants.py`).
                    *   Reads patterns from `project_root/.gitignore`.
                        *   Skips comments and empty lines.
                        *   Specifically ensures `.Q` itself is NOT ignored if listed (e.g. `/.Q/` in gitignore).
                        *   Strips leading/trailing slashes for `tree -I` format.
                    *   Deduplicates ignore patterns.
                *   Executes `tree` command in `project_root` using `subprocess.run()`.
                *   Captures stdout for `QX_PROJECT_FILES`.
                *   Handles `FileNotFoundError` for `tree` command and other execution errors.
            *   If `Path.cwd()` is `USER_HOME_DIR`, `QX_PROJECT_FILES` is set to an empty string.
            *   Sets `QX_PROJECT_FILES` environment variable.
    *   Added `if __name__ == "__main__":` block for testing `load_runtime_configurations()`.
2.  **Created `src/qx/core/constants.py`:**
    *   Defined `DEFAULT_TREE_IGNORE_PATTERNS` list with common directories/files to ignore (e.g., `.git`, `.venv`, `node_modules`, `__pycache__`).
3.  **Modified `src/qx/core/llm.py` (`initialize_llm_agent`):**
    *   Calls `load_runtime_configurations()` at the beginning.
    *   Retrieves `QX_USER_CONTEXT`, `QX_PROJECT_CONTEXT`, `QX_PROJECT_FILES` from `os.environ.get()`.
    *   Formats the system prompt string with these retrieved context variables.
4.  **Modified `src/qx/main.py`:**
    *   Removed the direct call to `load_runtime_configurations()` as it's now called within `initialize_llm_agent()`. *Correction during implementation: Decided to keep `load_runtime_configurations()` in `main.py` before `initialize_llm_agent` to ensure env vars are set globally first.*

**Testing:**
*   Manually created dummy `~/.config/q/user.md`, `project/.Q/project.md`, and `project/.gitignore`.
*   Ran `python -m src.qx.core.config_manager` to test context loading.
*   Ran the main QX application from different directories (project root, subdirectory, home directory) to verify context and file tree generation.

**Next Steps:**

*   Refine path restriction security for `read_file` and `write_file`.
*   Update `.Q/projectlog.md` with this sprint's details.
*   Commit changes.

---
## Sprint 7: Path Restriction Security for File Tools (Done)

**Date:** 2024-07-17

**Objective:** Enhance security for `read_file` and `write_file` tools by restricting operations to the project directory or user's home directory if no project is found.

**Tasks Completed:**

1.  **Modified `src/qx/core/config_manager.py`:**
    *   No direct changes for this sprint, but `_find_project_root` and `USER_HOME_DIR` are crucial.
2.  **Modified `src/qx/tools/file_operations_base.py` (New File):**
    *   Created a base module for common file operation logic.
    *   Imported `_find_project_root` and `USER_HOME_DIR` from `src.qx.core.config_manager`.
    *   **`is_path_allowed(resolved_path: Path, project_root: Optional[Path], user_home: Path) -> bool` function:**
        *   Takes the resolved absolute path of the file/directory to be accessed.
        *   Takes the determined `project_root` (can be `None`).
        *   Takes `user_home` path.
        *   **Logic:**
            *   If `project_root` exists:
                *   Path is allowed if it's within `project_root` OR if it's within `project_root / ".Q"`.
            *   If `project_root` does not exist (e.g., running QX from outside a project):
                *   Path is allowed if it's within `user_home`.
            *   Otherwise, the path is disallowed.
        *   This prevents traversal outside the determined scope.
3.  **Modified `src/qx/tools/read_file.py`:**
    *   Imported `is_path_allowed` and relevant path utilities from `file_operations_base`.
    *   Imported `_find_project_root`, `USER_HOME_DIR` from `src.qx.core.config_manager`.
    *   In `read_file(path_str: str)`:
        *   Determine `project_root = _find_project_root(str(Path.cwd()))`.
        *   Resolve `path_str` to `absolute_path = Path(path_str).resolve()`.
        *   Call `is_path_allowed(absolute_path, project_root, USER_HOME_DIR)`.
        *   If not allowed, print an error and return `None`.
        *   Proceed with file reading only if allowed.
4.  **Modified `src/qx/tools/write_file.py`:**
    *   Imported `is_path_allowed` and relevant path utilities from `file_operations_base`.
    *   Imported `_find_project_root`, `USER_HOME_DIR` from `src.qx.core.config_manager`.
    *   In `write_file(path_str: str, content: str)`:
        *   Determine `project_root = _find_project_root(str(Path.cwd()))`.
        *   Resolve `path_str` to `absolute_path = Path(path_str).resolve()`.
        *   Call `is_path_allowed(absolute_path, project_root, USER_HOME_DIR)`.
        *   If not allowed, print an error and return `False`.
        *   Proceed with file writing only if allowed.
        *   When creating parent directories with `os.makedirs`, ensure the directory path itself is also checked by `is_path_allowed(absolute_path.parent, project_root, USER_HOME_DIR)`.

**Refinement during implementation:**
*   The `is_path_allowed` function was simplified. If a `project_root` is identified, operations are confined to that root. If no `project_root` is found, operations are confined to the `USER_HOME_DIR`. This makes the logic clearer. Access to `.Q` within the project root is implicitly allowed if the path is within `project_root`.
*   The check for `absolute_path.parent` in `write_file` was deemed important to ensure directory creation also respects the boundaries.

**Next Steps:**
*   Update project log.
*   Commit changes.
*   Consider more granular permissions within `.Q` if needed in the future.

---

## Sprint 8: Conversation History (PydanticAI v0.2.3) (Done)

**Date:** 2024-07-18

**Objective:** Implement conversation history persistence across multiple turns using PydanticAI's built-in capabilities.

**Tasks Completed:**

1.  **`src/qx/core/llm.py` (`query_llm` function):**
    *   Imported `List`, `Optional` from `typing`.
    *   Imported `ModelMessage` from `pydantic_ai.messages`. (Note: `AgentRunResult` is already imported in `main.py` for type hinting, but `ModelMessage` is needed here for the `message_history` parameter).
    *   Modified the `query_llm` function signature to accept `message_history: Optional[List[ModelMessage]] = None`.
    *   Passed this `message_history` to `agent.run(user_input, message_history=message_history)`.
    *   The function now returns the entire `AgentRunResult` object instead of just `result.output`. This is necessary to access `result.new_messages()` or `result.all_messages()`.
2.  **`src/qx/main.py` (`_async_main` function):**
    *   Imported `List`, `Optional` from `typing` and `ModelMessage` from `pydantic_ai.messages`.
    *   Initialized `current_message_history: Optional[List[ModelMessage]] = None` before the main `while` loop.
    *   In the loop, after receiving `user_input`:
        *   Called `query_llm(agent, user_input, message_history=current_message_history)`.
        *   If `run_result` is not `None` (i.e., the call was successful):
            *   Printed `run_result.output` as the QX response.
            *   Updated `current_message_history = run_result.all_messages()`.
                *   **PydanticAI v0.2.3 Note:** The documentation examples for `message_history` often use `result.new_messages()`. However, to build a complete history for subsequent calls, `result.all_messages()` is more appropriate as it includes the system prompt, user prompt, and the latest assistant response, forming a complete chain. `new_messages()` typically returns only the latest request/response pair. For QX's purpose of maintaining full context, `all_messages()` is the choice.
        *   If `run_result` is `None` (error occurred):
            *   Printed an error message.
            *   Kept `current_message_history` as is (or could be set to `None` to reset on error, current choice is to keep).

**Next Steps:**

*   Thoroughly test conversation continuity.
*   Update project log.
*   Commit changes.

---

## Sprint 9: Update PydanticAI and Refactor Conversation History (Done)

**Date:** 2024-07-18

**Objective:** Update PydanticAI to the latest version (0.2.4) and refactor conversation history to use `run_result.all_messages()` for more robust context.

**Tasks Completed:**

1.  **Update PydanticAI:**
    *   Modified `pyproject.toml` to `pydantic-ai>=0.2.4`.
    *   Ran `uv pip install -r requirements.txt` (or equivalent `uv pip sync`) to update the lock file and environment.
2.  **Refactor Conversation History in `src/qx/main.py`:**
    *   In `_async_main`, changed the line for updating history from `current_message_history = run_result.new_messages()` to `current_message_history = run_result.all_messages()`.
    *   This ensures that the entire conversation context, including system prompts and all prior turns, is passed to the agent in subsequent calls, which is generally better for maintaining coherent long conversations. `new_messages()` typically only provides the last user-request and model-response pair.
3.  **Type Hinting Adjustments:**
    *   Ensured `AgentRunResult` is correctly imported and used for type hinting `run_result` in `src/qx/main.py`.
    *   Ensured `ModelMessage` is imported in both `src/qx/core/llm.py` and `src/qx/main.py` for `message_history` type hints.

**Rationale for `all_messages()`:**
Using `all_messages()` provides the LLM with the most complete context of the interaction so far. While `new_messages()` is useful for specific scenarios (like only wanting the immediate last exchange), for an ongoing agent conversation, `all_messages()` is generally preferred to avoid loss of context over multiple turns. PydanticAI handles the construction of the message list correctly for the LLM.

**Next Steps:**

*   Add dev dependencies (e.g., ipython) to `pyproject.toml`.
*   Commit changes.

---

## Sprint 10: Add Dev Dependencies and Centralize .env Loading (Done)

**Date:** 2024-07-19

**Objective:** Add `ipython` as a development dependency and centralize the loading of the project's `.env` file into `config_manager.py`.

**Tasks Completed:**

1.  **Add Dev Dependencies:**
    *   Modified `pyproject.toml` to include a `[tool.uv.sources]` or `[dependency-groups]` (preferred for newer `uv` versions) section for development dependencies.
    *   Added `ipython>=9.2.0` (or a suitable version) to this dev group.
    *   Updated `uv.lock` by running `uv pip compile pyproject.toml -o requirements.txt` then `uv pip sync requirements.txt` or directly `uv pip sync` if `uv` supports direct `pyproject.toml` dev group syncing.
2.  **Centralize `.env` Loading:**
    *   **`src/qx/core/config_manager.py` (`load_runtime_configurations` function):**
        *   Modified to load the project-specific `.env` file (e.g., `project_root/.env`).
        *   This loading occurs *after* loading the user-global `~/.config/q/q.conf`.
        *   Used `load_dotenv(dotenv_path=project_env_path, override=True)` for the project `.env` to ensure its variables can take precedence over those in `q.conf`.
        *   Updated docstrings to reflect the new loading order and source.
        *   Enhanced the `if __name__ == "__main__":` test block to simulate a project `.env` file and verify that its variables (especially overriding ones like `QX_MODEL_NAME`) are correctly loaded.
    *   **`src/qx/main.py`:**
        *   Removed the direct `from dotenv import load_dotenv` and `load_dotenv()` call.
        *   Ensured `from .core.config_manager import load_runtime_configurations` is present.
        *   Called `load_runtime_configurations()` at the very beginning of the script, before any environment variables are accessed. This ensures all configurations, including those from the project `.env`, are loaded before they are used to initialize the agent or display info.

**Next Steps:**

*   Update project log.
*   Commit changes.

---
## Sprint 11: Resolve Import Errors for Packaged Application (Done)

**Date:** 2024-07-19

**Objective:** Fix `ModuleNotFoundError` related to imports within the `qx` package when the application is run as an installed script.

**Tasks Completed:**

1.  **Initial Problem:**
    *   A `ModuleNotFoundError: No module named 'src'` occurred in `src/qx/core/config_manager.py` when importing `DEFAULT_TREE_IGNORE_PATTERNS` using `from src.qx.core.constants import ...`. This absolute import style is incorrect when the code is running from within the `src` directory or as part of the `qx` package.
2.  **First Attempted Fix (Relative Import):**
    *   Changed the import in `src/qx/core/config_manager.py` to `from .constants import DEFAULT_TREE_IGNORE_PATTERNS`.
    *   This is a common way to handle intra-package imports and works when Python recognizes `qx.core` as a package.
3.  **Second Attempted Fix (Absolute Package Import):**
    *   Based on user feedback preferring absolute imports and further analysis of Python's import mechanism for packages, the import was changed to `from qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS`.
    *   This style assumes that the `src` directory is in `sys.path` (often managed by `uv run` or by installing the package) and `qx` is the top-level package being imported from. This is the standard way to perform absolute imports within a package.

**Rationale for `from qx.core.constants ...`:**
When the project is installed or run in a way that `src` is added to `PYTHONPATH` (or `sys.path`), Python's import system can resolve `qx` as a top-level package. Imports within the `qx` package can then use `qx.` as their base. This is generally more robust for packaged applications compared to relative imports, which can sometimes behave differently depending on how a script is executed.

**Next Steps:**

*   Thoroughly test the application after installation (`uv pip install .`) to ensure all imports resolve correctly.
*   Update project log.
*   Commit changes.