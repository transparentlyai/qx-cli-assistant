# Console Manager - Producer-Consumer Pattern for Concurrent Console Access

## Overview

The Console Manager implements a producer-consumer pattern that allows multiple concurrent processes to safely access console output and input functionality without conflicts. This ensures orderly console interactions while maintaining full compatibility with the existing Rich theming and approval systems.

## Architecture

### Core Components

1. **Command Queue**: Thread-safe queue (`queue.Queue`) that holds console commands from producer processes
2. **Console Manager**: Dedicated consumer thread that processes commands sequentially  
3. **Command Types**: Different types of console operations (print, input, approval requests)
4. **Producer Processes**: Any code that needs console access (plugins, streaming, approvals)

### Command Types

- **PrintCommand**: For console output with Rich styling
- **InputCommand**: For simple text input requests (with optional defaults)
- **ApprovalRequestCommand**: For user approval requests (y/n/a/c pattern)
- **ChoiceSelectionCommand**: For multiple choice selections
- **ShutdownCommand**: For graceful manager shutdown

## Key Features

### Concurrent Access Patterns

#### 1. Blocking Pattern (Current Tools)
```python
# Tool blocks until user responds
approval = console_manager.request_approval_blocking("Approve execution?")
if approval[0] == "approved":
    execute_command()

# Simple input request
name = console_manager.request_input_blocking("Enter your name:")
```

#### 2. Non-blocking with Callback (Future Tools)
```python
# Tool continues, callback handles response
def handle_approval(response):
    if response[0] == "approved":
        execute_command()

def handle_input(response):
    print(f"User entered: {response}")

console_manager.request_approval_async("Approve execution?", callback=handle_approval)
console_manager.request_input_async("Enter configuration:", callback=handle_input)
# Tool continues other work while waiting...
```

#### 3. Non-blocking with Polling (Future Tools)  
```python
# Tool can check status periodically
request_id = console_manager.request_input_async("Enter value:", callback=None)
# Do other work...
if console_manager.is_response_ready(request_id):
    response = console_manager.get_response(request_id)
```

### Thread Safety

- All console interactions are serialized through the command queue
- Multiple concurrent processes can safely request console access
- No console output mixing or race conditions
- Maintains Rich theming and styling across all interactions

### Backward Compatibility

- Existing code continues to work unchanged
- Automatic fallback to direct console usage if manager unavailable
- All Rich theming and styling preserved
- ApprovalHandler maintains same API

## Integration Points

### Files Modified

1. **`console_manager.py`** - New core implementation
2. **`approval_handler.py`** - Updated to use console manager optionally
3. **`user_prompts.py`** - Updated key print statements with managed printing
4. **`streaming.py`** - Updated status messages to use console manager
5. **`execute_shell_plugin.py`** - Updated to use managed printing
6. **`write_file_plugin.py`** - Updated to use managed printing

### Preserved Systems

- **Main prompt** (`inline_mode.py`) - Uses prompt_toolkit, completely unaffected
- **Rich theming** - All custom themes and styling preserved
- **Global hotkeys** - Suspension/resumption during prompts maintained
- **Signal handling** - Ctrl+C management preserved
- **Environment variables** - All existing behavior controls maintained

## Usage Examples

### Basic Console Output

```python
from qx.core.console_manager import get_console_manager

manager = get_console_manager()

# Thread-safe printing
manager.print("[green]Success![/green]")
manager.print("Error occurred", style="error")

# Printing with source identifier
manager.print("Task completed", source_identifier="TaskRunner")
# Output: [TaskRunner] Task completed
```

### Simple Input Requests

```python
# Blocking input request
name = manager.request_input_blocking("Enter your name:")

# Input with default value
port = manager.request_input_blocking("Enter port:", default="8080")

# Input with source identifier
config = manager.request_input_blocking(
    "Enter database URL:",
    source_identifier="ConfigManager"
)
# Prompt: [ConfigManager] Enter database URL:

# Async input request
def handle_response(response):
    print(f"User entered: {response}")

manager.request_input_async(
    "Enter value:",
    callback=handle_response,
    source_identifier="AsyncService"
)
```

### Approval Requests

```python
# Blocking approval (current pattern)
result = manager.request_approval_blocking(
    prompt_message="Execute shell command?",
    console=themed_console,
    content_to_display=command_preview,
    source_identifier="ShellPlugin"
)
# Prompt: [ShellPlugin] Execute shell command? (y/n/a/c):

if result[0] == "approved":
    # Execute operation
    pass

# Async approval with callback
def handle_approval(response):
    if response[0] == "approved":
        execute_operation()

manager.request_approval_async(
    "Delete file?",
    console=themed_console,
    callback=handle_approval,
    source_identifier="FileManager"
)
```

### Choice Selection

```python
# Multiple choice selection
choice = manager.request_choice_blocking(
    prompt_text_with_options="Choose environment:",
    valid_choices=["dev", "staging", "prod"],
    console=themed_console,
    default_choice="dev",
    source_identifier="DeployManager"
)
# Prompt: [DeployManager] Choose environment:

# Async choice selection
def handle_choice(response):
    print(f"Selected: {response}")

manager.request_choice_async(
    "Select log level:",
    ["debug", "info", "warn", "error"], 
    console=themed_console,
    callback=handle_choice,
    source_identifier="LogConfig"
)
```

### Plugin Integration

```python
# Plugins use helper function for automatic fallback
def _managed_plugin_print(content: str, source_id: str = None, **kwargs) -> None:
    try:
        from qx.core.console_manager import get_console_manager
        manager = get_console_manager()
        if manager and manager._running:
            manager.print(content, console=themed_console, 
                         source_identifier=source_id, **kwargs)
            return
    except Exception:
        pass
    
    # Fallback to direct console usage
    if source_id:
        content = f"[{source_id}] {content}"
    themed_console.print(content, **kwargs)

# Plugin usage
_managed_plugin_print("Operation completed", source_id="MyPlugin")
```

## Configuration

### Environment Variables

All existing environment variables continue to work:

- `QX_AUTO_APPROVE` - Auto-approve all requests
- `QX_SHOW_SPINNER` - Control spinner display
- `QX_SHOW_STDOUT/STDERR` - Control output visibility

### Manager Lifecycle

```python
# Global manager automatically starts when first accessed
manager = get_console_manager()

# Manual shutdown for cleanup
shutdown_console_manager()
```

## Error Handling

### Circular Dependency Prevention

The system prevents circular dependencies between the console manager and user_prompts:

```python
# In user_prompts.py - disabled when called from ConsoleManager
_disable_console_manager = False

def _managed_print(console, content, **kwargs):
    if _disable_console_manager:
        console.print(content, **kwargs)  # Direct print
        return
    # Try console manager...
```

### Fallback Behavior

- If console manager not running: falls back to direct console usage
- If manager encounters errors: graceful degradation to direct printing
- Timeout handling for blocking operations
- Exception recovery with proper error logging

## Performance Considerations

### Optimized for Use Cases

- **Print operations**: Very fast queuing with minimal overhead
- **Real-time streaming**: Direct console access for performance-critical content
- **Status messages**: Queued for thread safety
- **Approval requests**: Optimized for user interaction responsiveness

### Memory Management

- Commands are processed and removed from queue immediately
- Response storage is cleaned up after retrieval
- Thread resources properly managed with daemon threads

## Testing

The system includes comprehensive test coverage:

### Test Categories

1. **Concurrent Prints** - Multiple workers printing simultaneously
2. **Concurrent Approvals** - Multiple approval requests queued safely  
3. **Non-blocking Callbacks** - Async approval with callback handling
4. **Mixed Operations** - Combined print and approval operations
5. **Fallback Behavior** - Graceful degradation when manager disabled

### Running Tests

```bash
python test_console_manager.py
```

Expected output shows orderly console interactions with no mixing or conflicts.

## Migration Guide

### For Existing Code

Most existing code requires no changes:

- **ApprovalHandler** - Works unchanged with new backend
- **Plugin outputs** - Automatically use console manager when available  
- **Streaming** - Performance-critical parts unchanged, status messages improved
- **User prompts** - Core functionality preserved with better concurrency

### For New Code

New concurrent tools can choose their interaction pattern:

```python
# Blocking input requests
name = manager.request_input_blocking("Enter name:", source_identifier="Setup")
approval = manager.request_approval_blocking("Continue?", console, source_identifier="Tool")
choice = manager.request_choice_blocking("Select:", options, console, source_identifier="Config")

# Non-blocking with callbacks
manager.request_input_async("Enter value:", handle_input, source_identifier="AsyncTool")
manager.request_approval_async("Approve?", console, handle_approval, source_identifier="Plugin")
manager.request_choice_async("Choose:", options, console, handle_choice, source_identifier="Service")
```

### Complete API Reference

All methods support optional `source_identifier` parameter for component attribution:

**Print Operations:**
- `print(content, style=None, markup=True, end="\n", console=None, source_identifier=None)`

**Input Operations:**
- `request_input_blocking(prompt_text, default=None, console=None, timeout=None, source_identifier=None)`
- `request_input_async(prompt_text, callback, default=None, console=None, source_identifier=None)`

**Approval Operations:**
- `request_approval_blocking(prompt_message, console, content_to_display=None, current_value_for_modification=None, default_choice_key="n", timeout=None, source_identifier=None)`
- `request_approval_async(prompt_message, console, callback, content_to_display=None, current_value_for_modification=None, default_choice_key="n", source_identifier=None)`

**Choice Operations:**
- `request_choice_blocking(prompt_text_with_options, valid_choices, console, default_choice=None, timeout=None, source_identifier=None)`
- `request_choice_async(prompt_text_with_options, valid_choices, console, callback, default_choice=None, source_identifier=None)`

## Source Identifier System

The ConsoleManager supports optional source identifiers to help users understand which component is making console requests.

### Benefits

- **Component Visibility**: Users can see which plugin/service is asking for input
- **Debugging Aid**: Easier to trace console interactions back to source code
- **Better UX**: Clear attribution of messages and prompts in concurrent environments

### Display Format

Source identifiers appear as dimmed tags before content:

```
[PluginName] Your message here
[ServiceName] Do you want to continue? (y/n)
[TaskRunner] Select option:
```

### Implementation

All console methods accept an optional `source_identifier` parameter:

```python
# Print operations
manager.print("Message", source_identifier="ComponentName")

# Input operations  
manager.request_input_blocking("Prompt:", source_identifier="ComponentName")
manager.request_input_async("Prompt:", callback, source_identifier="ComponentName")

# Approval operations
manager.request_approval_blocking("Approve?", console, source_identifier="ComponentName")
manager.request_approval_async("Approve?", console, callback, source_identifier="ComponentName")

# Choice operations
manager.request_choice_blocking("Choose:", choices, console, source_identifier="ComponentName")
manager.request_choice_async("Choose:", choices, console, callback, source_identifier="ComponentName")
```

## Benefits

### Immediate Benefits

- **Thread Safety**: No more console output conflicts
- **Orderly Interactions**: All console access serialized properly
- **Preserved Functionality**: Everything works exactly as before
- **Component Attribution**: Clear identification of message/prompt sources

### Future Benefits

- **Concurrent Tools**: New tools can safely run in parallel
- **Better UX**: No mixed console output during concurrent operations
- **Scalability**: System ready for more complex concurrent workflows
- **Enhanced Debugging**: Easy tracing of console interactions

## Implementation Details

### Producer-Consumer Flow

1. **Producer** creates command and adds to queue
2. **Consumer thread** pulls command from queue
3. **Consumer** executes command (print or request input)
4. **For input commands**: Consumer gets user response
5. **Response delivery**: Via blocking queue or async callback
6. **Cleanup**: Command processed, response delivered

### Thread Architecture

- **Main Thread**: Application logic, produces commands
- **Consumer Thread**: Dedicated console interaction thread
- **Worker Threads**: Various concurrent processes producing commands
- **Coordination**: Thread-safe queue and response mechanisms

This architecture ensures clean separation of concerns while maintaining all existing functionality and enabling future concurrent capabilities.