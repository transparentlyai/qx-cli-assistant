#!/usr/bin/env python3
import os

# Get all Python files to check
files_to_check = [
    "src/qx/cli/commands.py",
    "src/qx/cli/completer.py",
    "src/qx/cli/console.py",
    "src/qx/cli/history.py",
    "src/qx/cli/qprompt.py",
    "src/qx/cli/quote_bar_component.py",
    "src/qx/cli/session_selector.py",
    "src/qx/cli/theme.py",
    "src/qx/cli/version.py",
    "src/qx/core/agent_loader.py",
    "src/qx/core/agent_manager.py",
    "src/qx/core/approval_handler.py",
    "src/qx/core/async_utils.py",
    "src/qx/core/autonomous_agent.py",
    "src/qx/core/config_manager.py",
    "src/qx/core/console_manager.py",
    "src/qx/core/constants.py",
    "src/qx/core/global_hotkeys.py",
    "src/qx/core/history_utils.py",
    "src/qx/core/hotkey_manager.py",
    "src/qx/core/http_client_manager.py",
    "src/qx/core/langgraph_model_adapter.py",
    "src/qx/core/langgraph_supervisor.py",
    "src/qx/core/langgraph_tool_adapter.py",
    "src/qx/core/llm.py",
    "src/qx/core/llm_components/config.py",
    "src/qx/core/llm_components/messages.py",
    "src/qx/core/llm_components/prompts.py",
    "src/qx/core/llm_components/streaming.py",
    "src/qx/core/llm_components/tools.py",
    "src/qx/core/llm_utils.py",
    "src/qx/core/logging_config.py",
    "src/qx/core/markdown_buffer.py",
    "src/qx/core/mcp_manager.py",
    "src/qx/core/output_control.py",
    "src/qx/core/paths.py",
    "src/qx/core/plugin_manager.py",
    "src/qx/core/schemas.py",
    "src/qx/core/session_manager.py",
    "src/qx/core/state_manager.py",
    "src/qx/core/team_manager.py",
    "src/qx/core/team_mode_manager.py",
    "src/qx/core/user_prompts.py",
    "src/qx/plugins/agent_manager_plugin.py",
    "src/qx/plugins/current_time_plugin.py",
    "src/qx/plugins/execute_shell_plugin.py",
    "src/qx/plugins/read_file_plugin.py",
    "src/qx/plugins/web_fetch_plugin.py",
    "src/qx/plugins/write_file_plugin.py",
]


# Convert file paths to module names
def file_to_module(filepath):
    # Remove .py extension and convert path to module format
    module = filepath.replace(".py", "").replace("/", ".")
    return module


# Get all possible import patterns for a module
def get_import_patterns(filepath):
    module = file_to_module(filepath)
    basename = os.path.basename(filepath).replace(".py", "")

    patterns = []
    # Full module import patterns
    patterns.append(f"import {module}")
    patterns.append(f"from {module} import")

    # Relative imports from parent modules
    parts = module.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        child = ".".join(parts[i:])
        patterns.append(f"from {parent} import {child}")

    # Just the basename imports
    patterns.append(f"import {basename}")
    patterns.append(f"from {basename} import")

    # Relative imports with dots
    patterns.append(f"from .{basename} import")
    patterns.append(f"from ..{basename} import")
    patterns.append(f"import .{basename}")
    patterns.append(f"import ..{basename}")

    # Dynamic imports
    patterns.append(f'"{module}"')
    patterns.append(f"'{module}'")
    patterns.append(f'"{basename}"')
    patterns.append(f"'{basename}'")

    return patterns


# Check if a module is imported anywhere
def is_imported(filepath, all_files):
    patterns = get_import_patterns(filepath)

    for file in all_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                for pattern in patterns:
                    if pattern in content:
                        return True, file, pattern
        except:
            pass

    return False, None, None


# Get all Python files in the project
all_python_files = []
for root, dirs, files in os.walk("."):
    # Skip hidden directories and __pycache__
    dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

    for file in files:
        if file.endswith(".py"):
            all_python_files.append(os.path.join(root, file))

# Check each file
print("Checking for unused Python files in src/qx...\n")
unused_files = []

for filepath in files_to_check:
    if os.path.exists(filepath):
        imported, where, pattern = is_imported(filepath, all_python_files)
        if not imported:
            unused_files.append(filepath)
            print(f"UNUSED: {filepath}")
        else:
            print(f"USED: {filepath} (imported in {where} with pattern '{pattern}')")

print(f"\n\nSummary: Found {len(unused_files)} unused files:")
for f in sorted(unused_files):
    print(f"  - {f}")
