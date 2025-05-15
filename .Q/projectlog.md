# QX Project Log

## Sprint 1: Initial Setup & Stage 1 Implementation

**Date:** 2024-07-16

**Objective:** Complete Stage 1: Basic CLI loop with PydanticAI and Vertex AI.

**Tasks Completed:**

1.  **Environment Setup (`.env`):**
    *   Created `.env` file.
    *   Added `QX_MODEL_NAME="google-vertex:gemini-2.0-flash"`.
    *   Added placeholder `QX_VERTEX_PROJECT_ID="your-gcp-project-id"`.
    *   Added placeholder `QX_VERTEX_LOCATION="your-gcp-region"`.
    *   Included a comment about `GOOGLE_APPLICATION_CREDENTIALS`.

2.  **Core Application (`src/main.py`):**
    *   Created `src/main.py`.
    *   Implemented main asynchronous loop using `asyncio`.
    *   Integrated `python-dotenv` to load environment variables (`QX_MODEL_NAME`, `QX_VERTEX_PROJECT_ID`, `QX_VERTEX_LOCATION`).
    *   Initialized PydanticAI `Agent` with `QX_MODEL_NAME`.
    *   Added basic error handling for missing environment variables and agent initialization.
    *   Used `rich.console.Console` and `rich.prompt.Prompt` for user interaction ("Q>" prompt).
    *   Implemented "exit" / "quit" commands to terminate the application.
    *   Handled `KeyboardInterrupt` for graceful exit.
    *   Agent execution (`agent.run()`) is called with user input, and the output is printed.

3.  **Dependency Management (`pyproject.toml` & `uv`):**
    *   Confirmed `pyproject.toml` already included `pydantic-ai[vertexai]>=0.2.3` and `python-dotenv>=1.1.0`. No changes were needed.
    *   Ran `uv sync` to ensure dependencies are correctly installed and `uv.lock` is up-to-date.

**Next Steps (Initial):**

*   User to update `.env` with actual `QX_VERTEX_PROJECT_ID` and `QX_VERTEX_LOCATION`.
*   User to set `GOOGLE_APPLICATION_CREDENTIALS` if not already configured in their environment.
*   Test the application by running `python src/main.py`.

---

## Sprint 2: Prompt Refactoring & UI Update

**Date:** 2024-07-16

**Objective:** Refactor prompt logic into a separate module and update the prompt symbol.

**Tasks Completed:**

1.  **Directory Structure:**
    *   Created `src/cli/` directory.
    *   Created `src/cli/__init__.py` to make `src/cli` a Python package.

2.  **Prompt Module (`src/cli/qprompt.py`):**
    *   Created `src/cli/qprompt.py`.
    *   Defined an asynchronous function `get_user_input(console: Console)`:
        *   Initially used `rich.prompt.Prompt.ask_async()`.
        *   Sets the prompt to `"[bold cyan]Q⏵[/bold cyan] "`.
        *   Returns the user's input string.

3.  **Main Application Update (`src/main.py`):**
    *   Modified `src/main.py` to import `get_user_input` from `src.cli.qprompt`.
    *   Replaced the direct `Prompt.ask()` call with `await get_user_input(console)`.
    *   Added `EOFError` handling in the main loop for graceful exit on Ctrl+D.

**Next Steps (Sprint 2):**

*   Test the application with the new prompt and refactored input logic.
*   Proceed to further development stages.

**Notes:**
*   The date in Sprint 1 has been set to a fixed past date for consistency as the log was just created. Future entries will use the current date.
*   The `Prompt.ask_async` method from `rich.prompt` was initially used in `qprompt.py`. This was later found to be incorrect.

---

## Sprint 3: Bug Fix - Async Prompt Handling

**Date:** 2024-07-16

**Objective:** Fix `AttributeError` related to `rich.prompt.Prompt.ask_async`.

**Tasks Completed:**

1.  **Prompt Module Update (`src/cli/qprompt.py`):**
    *   Imported `asyncio`.
    *   Modified `get_user_input` function to use `await asyncio.to_thread(rich.prompt.Prompt.ask, ...)` instead of `Prompt.ask_async`. This correctly runs the synchronous `Prompt.ask` in a separate thread to avoid blocking the asyncio event loop.

**Next Steps (Sprint 3):**

*   Test the application to confirm the fix for `AttributeError`.
*   Continue with planned development.

**Notes:**
*   The `rich.prompt.Prompt` class does not have an `ask_async` method. The synchronous `ask` method must be used with `asyncio.to_thread` in an async context.

---

## Sprint 4: Switch to prompt_toolkit for Input

**Date:** 2024-07-16

**Objective:** Replace `rich.prompt` with `prompt_toolkit.shortcuts.prompt` for user input.

**Tasks Completed:**

1.  **Dependency Management (`pyproject.toml` & `uv`):**
    *   Added `prompt-toolkit>=3.0.0` to `pyproject.toml`.
    *   Ran `uv sync` to install the new dependency and update `uv.lock`.
    *   Noted a warning: `The package pydantic-ai==0.2.3 does not have an extra named vertexai`. This will be reviewed later if necessary.

2.  **Prompt Module Update (`src/cli/qprompt.py`):**
    *   Imported `prompt` from `prompt_toolkit.shortcuts` and `HTML` from `prompt_toolkit.formatted_text`.
    *   Modified `get_user_input` function:
        *   Replaced `rich.prompt.Prompt.ask` with `prompt_toolkit.shortcuts.prompt`.
        *   The prompt string `"[bold cyan]Q⏵[/bold cyan] "` is now created using `HTML('<style fg="ansicyan" bold="true">Q⏵ </style>')` for `prompt_toolkit`.
        *   Continues to use `await asyncio.to_thread` for the synchronous `prompt_toolkit.shortcuts.prompt`.
        *   The `console: Console` argument is kept in the function signature for potential future use, though `prompt_toolkit.shortcuts.prompt` doesn't use it directly for basic prompting.

**Next Steps (Sprint 4):**

*   Test the application with `prompt_toolkit` for input.
*   Review the `pydantic-ai[vertexai]` dependency warning.
*   Continue with planned development.

---

## Sprint 5: Refactor LLM Logic to Core Module

**Date:** 2024-07-16

**Objective:** Modularize LLM (PydanticAI) interaction into `src/core/llm.py`.

**Tasks Completed:**

1.  **Directory Structure:**
    *   Created `src/core/` directory.
    *   Created `src/core/__init__.py` to make `src/core` a Python package.

2.  **LLM Module (`src/core/llm.py`):**
    *   Created `src/core/llm.py`.
    *   Defined `initialize_llm_agent()`:
        *   Retrieves `QX_MODEL_NAME` from `os.getenv`.
        *   Initializes and returns a PydanticAI `Agent` instance.
        *   Includes basic error handling and console logging for initialization status.
    *   Defined `async def query_llm(agent: Agent, user_input: str)`:
        *   Takes an `Agent` instance and user input.
        *   Calls `await agent.run(user_input)`.
        *   Returns the `result.output` or an error message string.

3.  **Main Application Update (`src/main.py`):**
    *   Modified `src/main.py` to import `initialize_llm_agent` and `query_llm` from `src.core.llm`.
    *   Agent initialization is now done by calling `initialize_llm_agent()`.
    *   LLM queries are now done by calling `await query_llm(agent, user_input)`.
    *   Adjusted main loop to handle the direct output or error string from `query_llm`.

**Next Steps (Sprint 5):**

*   Test the application with the refactored LLM logic.
*   Continue with planned development.

---

## Sprint 6: Code Cleanup - Remove Development Artifacts

**Date:** 2024-07-17

**Objective:** Remove unnecessary comments that were artifacts of previous development steps.

**Tasks Completed:**

1.  **`src/main.py` Cleanup:**
    *   Removed comments like `# Removed: ...` and `# Added import` that were related to previous refactoring steps.

2.  **`src/cli/qprompt.py` Cleanup:**
    *   Removed a redundant comment `# For styled prompt` from an import line.
    *   Retained comments explaining the translation from Rich markup to `prompt_toolkit` HTML and the use of `asyncio.to_thread`, as they provide useful context.
    *   Clarified the docstring comment regarding the `console` argument.

3.  **`src/core/llm.py` Cleanup:**
    *   Removed comments like `# For potential logging...`, `# Local console...`, and `# For logging/checking`.
    *   Removed a commented-out `console.print` line.
    *   Retained a comment explaining why environment variables are checked in this module despite being checked in `main.py`.

**Next Steps:**

*   Review code for any further cleanup opportunities.
*   Continue with planned development.

---

## Sprint 7: Project Restructuring for Packaging

**Date:** 2024-07-17

**Objective:** Restructure the project to place the main application code within a `qx` package inside `src` for better organization and standard packaging practices.

**Tasks Completed:**

1.  **Directory Structure Changes:**
    *   Created the main package directory: `src/qx`.
    *   Moved `src/main.py` to `src/qx/main.py`.
    *   Moved the `src/core` directory to `src/qx/core`.
    *   Moved the `src/cli` directory to `src/qx/cli`.
    *   Created `src/qx/__init__.py` to mark `src/qx` as a Python package.

2.  **Configuration Update (`pyproject.toml`):**
    *   Updated the script entry point from `qx = "src.main:main"` to `qx = "qx.main:main"`.
    *   Added `[tool.setuptools.packages.find]` section with `where = ["src"]` to guide `setuptools` in discovering the `qx` package within the `src` directory.

3.  **Import Statement Adjustments:**
    *   In `src/qx/main.py`:
        *   Changed `from cli.qprompt import ...` to `from .cli.qprompt import ...`.
        *   Changed `from core.llm import ...` to `from .core.llm import ...`.
    *   No import changes were needed in `src/qx/cli/qprompt.py` or `src/qx/core/llm.py` as they did not have internal project imports affected by this level of restructuring.
    *   Updated comments in `src/qx/core/__init__.py` and `src/qx/cli/__init__.py` to reflect their new paths.

**Next Steps:**

*   Test the application thoroughly after restructuring (e.g., by installing with `uv pip install .` and running the `qx` command).
*   Commit the changes.