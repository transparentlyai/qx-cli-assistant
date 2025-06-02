# Qx - Coding CLI Agent

Qx is a command-line interface (CLI) agent designed to assist with software development, DevOps tasks, and code interaction within your project workspace. It is built using Python and the PydanticAI framework.

## Features
*(To be filled in as project progresses)*

## Installation & Setup
*(To be filled in as project progresses)*

## Usage
*(To be filled in as project progresses)*

## Plugins

QX's functionality is extended through a plugin system. Plugins are Python modules that define tools the agent can use to perform various actions.

### Creating a New Plugin

To create a new plugin for QX, follow these steps:

1.  **File Location**:
    *   Create a new Python file for your plugin in the `src/qx/plugins/` directory (e.g., `my_new_plugin.py`).

2.  **Pydantic Models for Input/Output**:
    *   Define Pydantic `BaseModel` classes for your plugin's inputs and outputs. This ensures type validation and clear data contracts.
    *   Use `Field(..., description="...")` for detailed descriptions of each field.

    ```python
    from pydantic import BaseModel, Field

    class MyPluginInput(BaseModel):
        parameter_name: str = Field(..., description="Description of this parameter.")
        # Add other parameters as needed

    class MyPluginOutput(BaseModel):
        result_value: str = Field(description="Description of the result.")
        # Add other output fields as needed
    ```

3.  **Tool Function Definition**:
    *   This is the main entry point for your plugin that PydanticAI will call.
    *   If your plugin needs access to shared Qx resources (like the console for printing messages, or configuration), include `ctx: RunContext[QXToolDependencies]` as the first argument.
    *   The second argument should be an instance of your input Pydantic model.
    *   The function must be type-hinted to return an instance of your output Pydantic model.

    ```python
    import logging
    from pydantic_ai import RunContext
    from qx.core.context import QXToolDependencies # For accessing console, etc.

    logger = logging.getLogger(__name__)

    def my_plugin_tool(
        ctx: RunContext[QXToolDependencies],
        args: MyPluginInput
    ) -> MyPluginOutput:
        console = ctx.deps.console # Example: get the Rich console
        console.print(f"Plugin received: {args.parameter_name}")
        logger.info(f"Executing my_plugin_tool with {args.parameter_name}")

        # --- Your plugin's core logic here ---
        processed_value = args.parameter_name.upper()
        # --- End of core logic ---

        return MyPluginOutput(result_value=f"Processed: {processed_value}")
    ```

4.  **Core Logic Separation (Recommended)**:
    *   For clarity and testability, consider placing the main operational code of your plugin into separate helper functions that your main tool function calls.

5.  **User Approvals and Interaction (If Applicable)**:
    *   For operations that modify the file system, execute shell commands, or perform other sensitive actions, always seek user approval.
    *   Use the `qx.core.user_prompts.request_confirmation` function.
    *   This function can display rich content (like file diffs or previews) for user review before approval.

    ```python
    # Inside your tool function, if confirmation is needed:
    # from qx.core.user_prompts import request_confirmation
    #
    # decision_status, final_value = request_confirmation(
    #     prompt_message=f"Allow plugin to process '{args.parameter_name}'?",
    #     console=console,
    #     # content_to_display=my_preview_renderable, # Optional: a Rich renderable
    # )
    #
    # if decision_status not in ["approved", "session_approved"]:
    #     logger.warning(f"Operation denied by user for {args.parameter_name}")
    #     return MyPluginOutput(result_value="Operation denied by user.")
    ```

6.  **Security Best Practices**:
    *   **File System Access**: If your plugin interacts with the file system, use path validation utilities (e.g., a centralized `is_path_allowed` function, which should be available in `qx.core.paths` or `qx.core.file_utils`) to restrict operations to the project directory or the user's home directory. Always confirm actions outside the immediate project scope.
    *   **Shell Commands**: If your plugin executes shell commands, be extremely cautious. Use `request_confirmation` and consider implementing pattern-based allow/deny lists similar to `execute_shell_plugin.py`.

7.  **Logging**:
    *   Use the standard Python `logging` module for diagnostic information.
    *   Obtain a logger instance: `logger = logging.getLogger(__name__)`.

8.  **Standalone Testing**:
    *   Include an `if __name__ == "__main__":` block at the end of your plugin file.
    *   This block should contain test cases that demonstrate and verify your plugin's functionality.
    *   Mock or create dummy versions of `RunContext` and `QXToolDependencies` as needed for testing.

    ```python
    if __name__ == "__main__":
        from rich.console import Console as RichConsole
        from qx.core.context import QXToolDependencies

        logging.basicConfig(level=logging.INFO)
        test_console = RichConsole()
        test_deps = QXToolDependencies(console=test_console)

        # Create a dummy RunContext
        class DummyRunContext(RunContext[QXToolDependencies]):
            def __init__(self, deps: QXToolDependencies):
                super().__init__(deps=deps, usage=None) # type: ignore
        dummy_ctx = DummyRunContext(deps=test_deps)

        # Test case 1
        test_input1 = MyPluginInput(parameter_name="test value")
        output1 = my_plugin_tool(dummy_ctx, test_input1)
        test_console.print(f"Test 1 Output: {output1}")
        assert "PROCESSED: TEST VALUE" in output1.result_value

        # Add more test cases
        test_console.print("MyNewPlugin tests finished.")
    ```

9.  **Plugin Registration**:
    *   After creating your plugin, you need to register its tool function with the PydanticAI agent.
    *   This typically involves adding your tool function to a list of tools that are passed to the agent upon its initialization. Look for files like `src/qx/main.py` or a dedicated plugin manager (e.g., `src/qx/core/plugin_manager.py`) for where to add your tool.
    *   (Example, actual registration might differ):
        ```python
        # In main.py or plugin_manager.py
        # from qx.plugins.my_new_plugin import my_plugin_tool
        #
        # active_tools = [
        #     # ... other tools
        #     my_plugin_tool,
        # ]
        # agent = PydanticAI(tools=active_tools, llm=...)
        ```

By following these guidelines, you can create new plugins that integrate smoothly with the Qx agent's architecture and adhere to its security and usability standards.
