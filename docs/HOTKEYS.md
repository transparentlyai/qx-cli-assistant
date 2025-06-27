# QX Global Hotkey System

This document describes QX's advanced global hotkey system that provides system-wide key capture capabilities.

## Overview

QX implements a sophisticated global hotkey system that allows users to trigger actions at any time during operation, including while the AI is processing responses. The system is built on top of the python-hotkeys library and provides conflict-free integration with prompt_toolkit.

## Available Hotkeys

### Core Hotkeys

| Hotkey | Action | Description |
|--------|--------|-------------|
| **F2** | Toggle Agent Mode | Switch between MULTI and SINGLE agent modes |
| **F3** | Toggle Details | Show/hide AI reasoning process during responses |
| **Ctrl+A / F5** | Toggle Approve All | Enable/disable automatic approval for tool operations |
| **F4** | Toggle StdOE | Show/hide stdout and stderr during tool execution |
| **F6** | Toggle Thinking Budget | Cycle through LOW/MEDIUM/HIGH thinking levels for supported models |
| **F1** | Toggle Mode | Switch between PLANNING and IMPLEMENTING modes |
| **Ctrl+R** | History Search | Search command history (available during input only) |
| **Ctrl+E** | Edit in External Editor | Open current input in text editor (vi by default, configurable via QX_DEFAULT_EDITOR). Supports: vi, vim, nvim, nano, code/vscode |
| **Ctrl+C** | Cancel Operation | Interrupt current operation |
| **Ctrl+D** | Exit Application | Gracefully exit QX |
| **F12** | Emergency Cancel | Alternative cancel option for emergency interruption |

### Hotkey Behavior

- **Global Activation**: Hotkeys work at any time, even during AI processing
- **Visual Feedback**: Each hotkey action provides immediate visual confirmation
- **Session Persistence**: Settings persist for the current session only
- **Safe Interruption**: Operations can be safely cancelled without data corruption

### Agent Mode System

QX supports two agent operation modes that control whether multiple agents can work together:

#### MULTI Mode (Default)
- **Purpose**: Enable collaboration between multiple specialized agents
- **Behavior**: Agents can delegate tasks to other agents via the invoke_agent tool
- **Use Cases**: Complex tasks requiring specialized expertise from different agents
- **Visual Indicator**: Blue "MULTI" badge in footer toolbar

#### SINGLE Mode
- **Purpose**: Restrict operation to a single agent only
- **Behavior**: Agent invocation is disabled, only the main agent operates
- **Use Cases**: Simple tasks, reduced complexity, focused single-agent operation
- **Visual Indicator**: Blue "SINGLE" badge in footer toolbar

**Mode Toggle**: Press **F2** to switch between MULTI and SINGLE agent modes at any time.

### Mode System

QX supports two distinct interaction modes that influence how the AI processes your requests:

#### PLANNING Mode
- **Purpose**: Focus on analysis, planning, and strategic thinking
- **Behavior**: All user messages include context indicator "The current mode is PLANNING"
- **Use Cases**: Project planning, problem analysis, architectural decisions
- **Visual Indicator**: Blue background in footer toolbar

#### IMPLEMENTING Mode (Default)
- **Purpose**: Focus on execution, coding, and implementation tasks
- **Behavior**: All user messages include context indicator "The current mode is IMPLEMENTING"
- **Use Cases**: Writing code, running commands, making changes
- **Visual Indicator**: Green background in footer toolbar

**Mode Toggle**: Press **F1** to switch between modes at any time. The current mode is always visible in the bottom toolbar and affects how the AI interprets and responds to your requests.

### Thinking Budget System

QX supports configurable thinking budget for models that accept the "thinking" parameter (e.g., Gemini 2.5 models):

#### Budget Levels
- **LOW (Default)**: Minimal thinking effort - faster responses, suitable for simple tasks
- **MEDIUM**: Balanced thinking effort - good for most use cases
- **HIGH**: Maximum thinking effort - best for complex reasoning tasks

#### Key Features
- **Model Support**: Only enabled for models that accept the "thinking" parameter
- **Session Scope**: Always starts at LOW for each new session (not persistent)
- **Visual Indicator**: Shows current level (LOW/MEDIUM/HIGH) in blue or DISABLED in grey
- **Dynamic Toggle**: Press **F6** to cycle through LOW → MEDIUM → HIGH → LOW

**Thinking Toggle**: Press **F6** to adjust the thinking budget. The current level is displayed in the footer toolbar and only works with supported models.

## Technical Architecture

### Core Components

#### 1. GlobalHotkeys Class (`src/qx/core/global_hotkeys.py`)

The low-level hotkey capture engine:

```python
class GlobalHotkeys:
    """
    A robust terminal hotkey handler using advanced parsing techniques.
    Based on patterns from prompt_toolkit for maximum compatibility.
    """
```

**Key Features:**
- **Terminal Input Capture**: Uses termios and tty for raw terminal input
- **State Machine Parser**: Handles multi-character escape sequences
- **Async/Sync Callbacks**: Supports both synchronous and asynchronous handlers
- **Performance Optimization**: Queue-based overflow protection and timeout handling

#### 2. QXHotkeyManager Class (`src/qx/core/hotkey_manager.py`)

The high-level hotkey management system:

```python
class QXHotkeyManager:
    """
    Manages hotkey action handlers for QX.
    
    This service provides centralized hotkey action handling with global
    hotkey capture that works at any time, not just during prompt input.
    """
```

**Key Features:**
- **Action Registry**: Centralized handler registration for hotkey actions
- **Global Integration**: Bridges low-level capture with QX functionality
- **Thread Safety**: Safe concurrent access to hotkey handlers

### Suspend/Resume Pattern

The system implements an intelligent suspend/resume pattern to prevent conflicts:

#### When Hotkeys Are Suspended

1. **User Input Prompts**: When prompt_toolkit is active for user input
2. **Tool Approval Dialogs**: During approval prompts to prevent accidental triggers
3. **Interactive Operations**: Any operation requiring user keyboard input

#### Implementation

```python
def _suspend_global_hotkeys():
    """Suspend global hotkeys during approval prompts."""
    try:
        from qx.core.hotkey_manager import get_hotkey_manager
        manager = get_hotkey_manager()
        if manager and manager.running:
            manager.stop()
            return True
    except Exception as e:
        logger.debug(f"Could not suspend global hotkeys: {e}")
    return False

def _resume_global_hotkeys():
    """Resume global hotkeys after approval prompts."""
    try:
        from qx.core.hotkey_manager import get_hotkey_manager
        manager = get_hotkey_manager()
        if manager and not manager.running:
            manager.start()
    except Exception as e:
        logger.debug(f"Could not resume global hotkeys: {e}")
```

## Key Sequence Parsing

The system uses a comprehensive ANSI sequence parser that supports:

### Supported Key Types

- **Control Characters**: Ctrl+A through Ctrl+Z
- **Function Keys**: F1-F12 with multiple terminal variations
- **Extended Function Keys**: F13-F24
- **Arrow Keys**: Up, Down, Left, Right (with modifiers)
- **Navigation Keys**: Home, End, Page Up, Page Down
- **Modifier Combinations**: Ctrl, Shift, Alt with other keys
- **Alt Combinations**: Alt+letter, Alt+number

### Terminal Compatibility

The parser handles multiple terminal emulator patterns:

```python
# Function key F1 examples
'\\x1bOP': 'f1',      # Standard xterm
'\\x1b[[A': 'f1',     # Linux console
'\\x1b[11~': 'f1',    # rxvt-unicode, some xterms
```

## Default Action Handlers

### Toggle Details Handler

```python
async def _default_toggle_details_handler():
    """Default handler for Ctrl+T - toggle details mode."""
    from qx.core.state_manager import show_details_manager
    from qx.core.config_manager import ConfigManager
    
    new_status = not await show_details_manager.is_active()
    await show_details_manager.set_status(new_status)
    
    # Update config and provide feedback
    config_manager = ConfigManager(themed_console, None)
    config_manager.set_config_value("QX_SHOW_DETAILS", str(new_status).lower())
    
    status_text = "enabled" if new_status else "disabled"
    themed_console.print(f"✓ [dim green]Details:[/] {status_text}.", style="warning")
```

### Approve All Handler

```python
async def _default_approve_all_handler():
    """Default handler for Ctrl+A - toggle approve all mode."""
    import qx.core.user_prompts as user_prompts
    
    async with user_prompts._approve_all_lock:
        user_prompts._approve_all_active = not user_prompts._approve_all_active
        status = "activated" if user_prompts._approve_all_active else "deactivated"
        
    themed_console.print(f"✓ [dim green]Approve All mode[/] {status}.", style="warning")
```

## Approval System Integration

### Approval Options

When QX requests permission for tool operations:

- **Y** (Yes): Approve this single operation
- **N** (No): Deny this operation  
- **A** (All): Activate "Approve All" mode for the session
- **C** (Cancel): Cancel the operation

### Approve All Mode

The "Approve All" feature:

1. **Activation**: Press 'A' during any tool approval OR use Ctrl+A hotkey
2. **Session Scope**: Mode persists until QX exits
3. **Visual Feedback**: Clear confirmation when activated/deactivated
4. **Bypass Logic**: Subsequent operations are auto-approved without prompts

### Implementation Details

The approval handler in `approval_handler.py` manages the flow:

```python
if chosen_key == "a":
    # Modify the global variable through the module to ensure consistency
    import qx.core.user_prompts as user_prompts
    async with _approve_all_lock:
        user_prompts._approve_all_active = True
    self.console.print(
        "[info]'Approve All' activated for this session.[/info]"
    )
```

## Performance Considerations

### Memory Management

- **Queue Size Limiting**: Unhandled keys queue limited to 1000 items
- **Overflow Protection**: Automatic queue cleanup when full
- **Thread Cleanup**: Proper thread termination on shutdown

### Input Filtering

The system filters input to avoid capturing regular text:

```python
if not (len(key) == 1 and key.isprintable()) and key not in [
    "enter", "return", "tab", "space", "backspace", "delete"
]:
    # Only capture special keys, not regular text input
    self.unhandled_keys_queue.put_nowait(key)
```

## Error Handling

### Graceful Degradation

- **Terminal Compatibility**: Fallback to prompt_toolkit-only mode if global capture fails
- **Error Logging**: Comprehensive debug logging for troubleshooting
- **Safe Defaults**: System continues to function even if hotkey capture fails

### Debug Mode

Enable detailed logging:

```bash
QX_LOG_LEVEL=DEBUG uv run qx
```

This provides detailed information about:
- Hotkey registration and detection
- Key sequence parsing
- Suspend/resume operations
- Callback execution

## Troubleshooting

### Common Issues

1. **Hotkeys Not Working**:
   - Ensure you're running in a proper TTY: `sys.stdin.isatty()` should return True
   - Check for terminal compatibility warnings in debug mode
   - Verify hotkey manager is started: should see "QX Hotkey Manager with global capture started"

2. **Conflicts with Other Tools**:
   - Global hotkeys are suspended during user input to prevent conflicts
   - Use prompt_toolkit hotkeys during input phases
   - F12 provides emergency cancel if other hotkeys conflict

3. **Performance Issues**:
   - Monitor queue size if experiencing input lag
   - Check for excessive key sequence logging in debug mode
   - Ensure proper thread cleanup on application exit

### Debug Commands

```bash
# Enable debug logging for hotkey system
QX_LOG_LEVEL=DEBUG uv run qx

# Check terminal compatibility
python -c "import sys; print('TTY:', sys.stdin.isatty())"

# Test basic hotkey functionality
# (Start QX and try Ctrl+T to toggle details mode)
```

## Future Enhancements

### Planned Features

- **Custom Hotkey Configuration**: User-defined hotkey mappings
- **Context-Sensitive Hotkeys**: Different hotkeys for different modes
- **Hotkey Chaining**: Composite key sequences (e.g., Ctrl+X, Ctrl+C)
- **Visual Hotkey Help**: On-screen hotkey reference

### Integration Opportunities

- **IDE Integration**: Hotkeys that work across terminal and editor
- **Workspace Management**: Hotkeys for project switching
- **Tool Chain Integration**: Hotkeys for external development tools

---

The QX global hotkey system represents a sophisticated approach to terminal-based user interaction, providing responsive control while maintaining compatibility with existing terminal applications and workflows.
