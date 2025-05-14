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

**Date:** $(date +'%Y-%m-%d')

**Objective:** Refactor prompt logic into a separate module and update the prompt symbol.

**Tasks Completed:**

1.  **Directory Structure:**
    *   Created `src/cli/` directory.
    *   Created `src/cli/__init__.py` to make `src/cli` a Python package.

2.  **Prompt Module (`src/cli/qprompt.py`):**
    *   Created `src/cli/qprompt.py`.
    *   Defined an asynchronous function `get_user_input(console: Console)`:
        *   Uses `rich.prompt.Prompt.ask_async()` for non-blocking input.
        *   Sets the prompt to `"[bold cyan]Q⏵[/bold cyan] "`.
        *   Returns the user's input string.

3.  **Main Application Update (`src/main.py`):**
    *   Modified `src/main.py` to import `get_user_input` from `src.cli.qprompt`.
    *   Replaced the direct `Prompt.ask()` call with `await get_user_input(console)`.
    *   Added `EOFError` handling in the main loop for graceful exit on Ctrl+D.

**Next Steps:**

*   Test the application with the new prompt and refactored input logic.
*   Proceed to further development stages.

**Notes:**
*   The date in Sprint 1 has been set to a fixed past date for consistency as the log was just created. Future entries will use the current date.
*   The `Prompt.ask_async` method from `rich.prompt` is used in `qprompt.py` as it's more suitable for an `asyncio` application than the synchronous `Prompt.ask`.