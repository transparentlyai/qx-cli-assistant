# QX Tool Development Guide

## Overview

This guide provides everything you need to know to create new tools for the QX LLM agent system. Tools are automatically discovered plugins that extend QX's capabilities, allowing the AI to interact with external systems, perform operations, and provide specialized functionality.

## Quick Start

### 1. Create Your Plugin File

Create a new file in `src/qx/plugins/` with the naming pattern `*_plugin.py`:

```python
# src/qx/plugins/my_awesome_plugin.py
import logging
from typing import Optional
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

logger = logging.getLogger(__name__)

class MyAwesomeInput(BaseModel):
    """Input parameters for the awesome tool."""
    message: str = Field(description="The message to process")
    count: int = Field(default=1, description="Number of times to process")

class MyAwesomeOutput(BaseModel):
    """Output from the awesome tool."""
    result: str = Field(description="The processed result")
    error: Optional[str] = None

async def my_awesome_tool(
    console: RichConsole, 
    args: MyAwesomeInput
) -> MyAwesomeOutput:
    """
    Process a message in an awesome way.
    
    This tool demonstrates basic plugin structure and patterns.
    """
    try:
        # Your tool logic here
        processed = f"Awesome: {args.message}" * args.count
        
        return MyAwesomeOutput(result=processed)
        
    except Exception as e:
        logger.error(f"MyAwesome tool failed: {e}", exc_info=True)
        return MyAwesomeOutput(
            result="", 
            error=f"Tool execution failed: {e}"
        )
```

### 2. Test Your Tool

Your tool is automatically discovered and available to the LLM immediately. Test it by asking QX to use your tool:

```
"Can you use the my_awesome tool to process the message 'Hello World' 3 times?"
```

## Tool Architecture

### File Structure

```
src/qx/plugins/
├── __init__.py
├── current_time_plugin.py      # Example: Simple parameterless tool  
├── execute_shell_plugin.py     # Example: Complex tool with approvals
├── read_file_plugin.py         # Example: File operations
├── write_file_plugin.py        # Example: File creation with previews
├── web_fetch_plugin.py         # Example: External API calls
└── your_new_plugin.py          # Your new tool
```

### Naming Conventions

- **File**: `your_tool_name_plugin.py`
- **Input Model**: `YourToolNameInput`
- **Output Model**: `YourToolNameOutput` or `YourToolNamePluginOutput`
- **Function**: `your_tool_name_tool()`

## Component Deep Dive

### Input Models

Input models define the parameters your tool accepts:

```python
class ComplexToolInput(BaseModel):
    """Comprehensive input example."""
    
    # Required parameter
    required_param: str = Field(description="This parameter is required")
    
    # Optional parameter with default
    optional_param: int = Field(default=10, description="Optional with default value")
    
    # Optional parameter that can be None
    nullable_param: Optional[str] = Field(default=None, description="Can be None")
    
    # Parameter with validation
    percentage: float = Field(
        default=50.0, 
        ge=0.0, 
        le=100.0, 
        description="Percentage between 0 and 100"
    )
    
    # Enum-like parameter
    mode: str = Field(
        default="standard",
        description="Processing mode: 'standard', 'advanced', or 'debug'"
    )
```

### Output Models

Output models define what your tool returns:

```python
class ComplexToolOutput(BaseModel):
    """Comprehensive output example."""
    
    # Primary result
    result: str = Field(description="The main result of the operation")
    
    # Additional data
    metadata: dict = Field(default_factory=dict, description="Additional operation metadata")
    
    # Success indicators
    success: bool = Field(default=True, description="Whether operation succeeded")
    
    # Error handling (ALWAYS include this)
    error: Optional[str] = None
    
    # Optional metrics
    duration_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    items_processed: Optional[int] = Field(default=None, description="Number of items processed")
```

### Tool Function

The main tool function follows a strict signature pattern:

```python
async def your_tool_name_tool(
    console: RichConsole, 
    args: YourToolInput
) -> YourToolOutput:
    """
    Brief description of what the tool does.
    
    Detailed description of functionality, use cases, and any
    important behavior that users should know about.
    
    Args:
        console: Rich console for output (automatically provided)
        args: Validated input parameters
        
    Returns:
        YourToolOutput: Results and any error information
    """
    # Implementation here
```

## User Approval System

For operations that require user consent, use the ApprovalHandler:

### Basic Approval

```python
from qx.core.approval_handler import ApprovalHandler
from qx.cli.console import themed_console

async def risky_operation_tool(
    console: RichConsole, 
    args: RiskyInput
) -> RiskyOutput:
    
    approval_handler = ApprovalHandler(themed_console)
    
    # Request user approval
    status, _ = await approval_handler.request_approval(
        operation="Risky Operation",
        parameter_name="target",
        parameter_value=args.target,
        prompt_message=f"Allow QX to perform risky operation on '{args.target}'?",
        content_to_display=preview_content  # Optional preview
    )
    
    if status not in ["approved", "session_approved"]:
        approval_handler.print_outcome("Operation", "Denied by user.", success=False)
        return RiskyOutput(error="Operation denied by user")
    
    try:
        # Perform the operation
        result = perform_risky_operation(args.target)
        approval_handler.print_outcome("Operation", "Completed successfully.")
        return RiskyOutput(result=result)
        
    except Exception as e:
        approval_handler.print_outcome("Operation", f"Failed: {e}", success=False)
        return RiskyOutput(error=str(e))
```

### Auto-Approval for Safe Operations

```python
def is_operation_safe(operation_params) -> bool:
    """Check if operation can be auto-approved."""
    # Your safety logic here
    return operation_params.is_read_only and operation_params.is_safe

async def smart_approval_tool(console: RichConsole, args: SmartInput) -> SmartOutput:
    approval_handler = ApprovalHandler(themed_console)
    
    if is_operation_safe(args):
        # Auto-approve safe operations
        themed_console.print(f"Safe Operation (Auto-approved): {args.operation}")
        status = "approved"
    else:
        # Request approval for risky operations
        status, _ = await approval_handler.request_approval(
            operation="Potentially Risky Operation",
            parameter_name="operation",
            parameter_value=args.operation,
            prompt_message=f"Allow QX to perform '{args.operation}'?"
        )
    
    # Continue with operation...
```

## Thread-Safe Console Output

For tools that may run concurrently, use thread-safe console output:

```python
def _managed_plugin_print(content: str, **kwargs) -> None:
    """Thread-safe console output helper."""
    try:
        from qx.core.console_manager import get_console_manager
        manager = get_console_manager()
        if manager and manager._running:
            style = kwargs.get('style')
            markup = kwargs.get('markup', True)
            end = kwargs.get('end', '\n')
            manager.print(content, style=style, markup=markup, end=end, console=themed_console)
            return
    except Exception:
        pass
    
    # Fallback to direct themed_console usage
    themed_console.print(content, **kwargs)

async def concurrent_safe_tool(console: RichConsole, args: Input) -> Output:
    # Use managed printing for thread safety
    _managed_plugin_print("[green]Starting operation...[/green]")
    
    try:
        result = await some_async_operation()
        _managed_plugin_print(f"[green]Operation completed: {result}[/green]")
        return Output(result=result)
        
    except Exception as e:
        _managed_plugin_print(f"[red]Operation failed: {e}[/red]")
        return Output(error=str(e))
```

## File Operations

For tools that work with files, follow security best practices:

```python
import os
from pathlib import Path
from qx.core.paths import USER_HOME_DIR, _find_project_root

def is_path_allowed(file_path: Path, project_root: str, user_home: str) -> bool:
    """Check if file path is allowed by security policy."""
    try:
        resolved_path = file_path.resolve()
        
        # Allow files within project root
        if str(resolved_path).startswith(project_root):
            return True
            
        # Allow files within user home (but not system directories)
        if str(resolved_path).startswith(user_home):
            # Block system-critical directories
            forbidden_dirs = ['.ssh', '.gnupg', '.config/sudo']
            for forbidden in forbidden_dirs:
                if f"/{forbidden}/" in str(resolved_path) or str(resolved_path).endswith(f"/{forbidden}"):
                    return False
            return True
            
        return False
        
    except Exception:
        return False

async def file_operation_tool(console: RichConsole, args: FileInput) -> FileOutput:
    approval_handler = ApprovalHandler(themed_console)
    
    # Validate and resolve path
    expanded_path = os.path.expanduser(args.path)
    absolute_path = Path(expanded_path).resolve()
    project_root = _find_project_root(str(Path.cwd()))
    
    # Security check
    if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
        error_msg = f"Access denied by policy for path: {absolute_path}"
        _managed_plugin_print(f"File Operation (Denied by Policy): {absolute_path}")
        approval_handler.print_outcome("Operation", "Failed. Policy violation.", success=False)
        return FileOutput(error=error_msg)
    
    # Continue with file operation...
```

## External API Integration

For tools that call external APIs:

```python
import asyncio
import httpx
from typing import Optional

async def api_tool(console: RichConsole, args: ApiInput) -> ApiOutput:
    """Tool that calls external API with proper error handling."""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Make API request
            response = await client.get(
                args.api_url,
                params=args.params,
                headers={"User-Agent": "QX-Agent/1.0"}
            )
            
            response.raise_for_status()
            
            # Process response
            data = response.json()
            
            return ApiOutput(
                data=data,
                status_code=response.status_code,
                success=True
            )
            
    except httpx.TimeoutException:
        error_msg = f"API request timed out after 30 seconds"
        logger.warning(error_msg)
        return ApiOutput(error=error_msg)
        
    except httpx.HTTPStatusError as e:
        error_msg = f"API returned error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        return ApiOutput(
            error=error_msg,
            status_code=e.response.status_code
        )
        
    except Exception as e:
        error_msg = f"API request failed: {e}"
        logger.error(error_msg, exc_info=True)
        return ApiOutput(error=error_msg)
```

## Tool Examples by Category

### 1. Information Retrieval (Simple)

```python
# current_time_plugin.py - Parameterless information tool
class CurrentTimeInput(BaseModel):
    pass

class CurrentTimeOutput(BaseModel):
    current_time: str = Field(description="Current date and time")
    timezone: str = Field(description="System timezone")

async def get_current_time_tool(console: RichConsole, args: CurrentTimeInput) -> CurrentTimeOutput:
    import datetime
    import time
    
    now = datetime.datetime.now()
    timezone = time.tzname[0]
    
    return CurrentTimeOutput(
        current_time=now.strftime("%Y-%m-%d %H:%M:%S"),
        timezone=timezone
    )
```

### 2. System Operations (With Approval)

```python
# system_operation_plugin.py - Tool requiring user approval
class SystemOpInput(BaseModel):
    command: str = Field(description="System command to execute")

class SystemOpOutput(BaseModel):
    output: str = Field(description="Command output")
    return_code: int = Field(description="Exit code")
    error: Optional[str] = None

async def system_operation_tool(console: RichConsole, args: SystemOpInput) -> SystemOpOutput:
    approval_handler = ApprovalHandler(themed_console)
    
    # Security check
    if is_dangerous_command(args.command):
        return SystemOpOutput(
            output="", 
            return_code=-1, 
            error="Command blocked by security policy"
        )
    
    # Get approval
    status, _ = await approval_handler.request_approval(
        operation="Execute System Command",
        parameter_name="command",
        parameter_value=args.command,
        prompt_message=f"Allow QX to execute: '{args.command}'?"
    )
    
    if status not in ["approved", "session_approved"]:
        return SystemOpOutput(
            output="", 
            return_code=-1, 
            error="Operation denied by user"
        )
    
    # Execute command
    import subprocess
    result = subprocess.run(
        args.command, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    return SystemOpOutput(
        output=result.stdout,
        return_code=result.returncode,
        error=result.stderr if result.stderr else None
    )
```

### 3. Data Processing (Complex)

```python
# data_processor_plugin.py - Complex tool with multiple options
class DataProcessorInput(BaseModel):
    data: list = Field(description="Data to process")
    operation: str = Field(description="Operation: 'sort', 'filter', 'transform'")
    options: dict = Field(default_factory=dict, description="Operation-specific options")

class DataProcessorOutput(BaseModel):
    processed_data: list = Field(description="Processed data")
    operation_performed: str = Field(description="Operation that was performed")
    items_processed: int = Field(description="Number of items processed")
    error: Optional[str] = None

async def data_processor_tool(console: RichConsole, args: DataProcessorInput) -> DataProcessorOutput:
    try:
        start_time = time.time()
        _managed_plugin_print(f"[blue]Processing {len(args.data)} items with operation '{args.operation}'[/blue]")
        
        if args.operation == "sort":
            key = args.options.get("key", None)
            reverse = args.options.get("reverse", False)
            processed = sorted(args.data, key=key, reverse=reverse)
            
        elif args.operation == "filter":
            condition = args.options.get("condition")
            processed = [item for item in args.data if eval_condition(item, condition)]
            
        elif args.operation == "transform":
            transformation = args.options.get("transformation")
            processed = [apply_transformation(item, transformation) for item in args.data]
            
        else:
            raise ValueError(f"Unknown operation: {args.operation}")
        
        duration = time.time() - start_time
        _managed_plugin_print(f"[green]Processed {len(processed)} items in {duration:.2f}s[/green]")
        
        return DataProcessorOutput(
            processed_data=processed,
            operation_performed=args.operation,
            items_processed=len(processed)
        )
        
    except Exception as e:
        logger.error(f"Data processing failed: {e}", exc_info=True)
        return DataProcessorOutput(
            processed_data=[],
            operation_performed=args.operation,
            items_processed=0,
            error=str(e)
        )
```

## Testing Your Tools

### 1. Unit Testing

Create tests for your tool logic:

```python
# tests/test_my_awesome_plugin.py
import pytest
from unittest.mock import MagicMock
from qx.plugins.my_awesome_plugin import my_awesome_tool, MyAwesomeInput

@pytest.mark.asyncio
async def test_my_awesome_tool_basic():
    console = MagicMock()
    args = MyAwesomeInput(message="test", count=2)
    
    result = await my_awesome_tool(console, args)
    
    assert result.error is None
    assert result.result == "Awesome: test" * 2

@pytest.mark.asyncio
async def test_my_awesome_tool_error_handling():
    console = MagicMock()
    args = MyAwesomeInput(message="", count=-1)  # Invalid input
    
    result = await my_awesome_tool(console, args)
    
    assert result.error is not None
    assert "failed" in result.error.lower()
```

### 2. Integration Testing

Test your tool through the LLM interface:

```python
# Ask QX to use your tool
user_prompt = "Use my_awesome_tool to process 'Hello World' 3 times"

# Expected behavior:
# 1. LLM recognizes the tool
# 2. Calls tool with correct parameters
# 3. Returns processed result
```

### 3. Manual Testing

```bash
# Start QX and test your tool
python -m qx

# Test various scenarios:
# - Valid inputs
# - Invalid inputs  
# - Edge cases
# - Error conditions
# - Approval flows (if applicable)
```

## Best Practices

### Security

1. **Always validate inputs** using Pydantic models
2. **Implement approval flows** for any operation that modifies system state
3. **Use path validation** for file operations
4. **Sanitize external inputs** before processing
5. **Follow principle of least privilege**

### Error Handling

1. **Always include error field** in output models
2. **Use structured error messages** that are helpful to users
3. **Log errors appropriately** with proper log levels
4. **Provide graceful degradation** when possible
5. **Don't expose sensitive information** in error messages

### User Experience

1. **Provide clear, descriptive field descriptions** in models
2. **Use meaningful operation names** in approval flows
3. **Give progress feedback** for long-running operations
4. **Use appropriate console styling** (colors, formatting)
5. **Make auto-approval decisions transparent**

### Performance

1. **Use async/await properly** for I/O operations
2. **Implement timeouts** for external API calls
3. **Use thread-safe console output** for concurrent tools
4. **Avoid blocking operations** in the main thread
5. **Cache results** when appropriate

### Documentation

1. **Write clear docstrings** for tool functions
2. **Document security considerations** and approval requirements
3. **Provide usage examples** in docstrings
4. **Explain side effects** and state changes
5. **Document error conditions** and recovery strategies

## Advanced Features

### Custom Approval Logic

```python
class CustomApprovalInput(BaseModel):
    operation_type: str
    risk_level: int = Field(ge=1, le=5, description="Risk level 1-5")

async def custom_approval_tool(console: RichConsole, args: CustomApprovalInput) -> Output:
    approval_handler = ApprovalHandler(themed_console)
    
    # Custom approval logic based on risk level
    if args.risk_level <= 2:
        # Auto-approve low-risk operations
        themed_console.print(f"Low-risk operation (Auto-approved): {args.operation_type}")
        status = "approved"
    elif args.risk_level == 3:
        # Standard approval for medium risk
        status, _ = await approval_handler.request_approval(
            operation="Medium Risk Operation",
            parameter_name="type",
            parameter_value=args.operation_type,
            prompt_message=f"Allow medium-risk operation '{args.operation_type}'?"
        )
    else:
        # Enhanced approval for high risk
        warning_content = f"⚠️  HIGH RISK OPERATION ⚠️\nOperation: {args.operation_type}\nRisk Level: {args.risk_level}/5"
        status, _ = await approval_handler.request_approval(
            operation="HIGH RISK Operation",
            parameter_name="type", 
            parameter_value=args.operation_type,
            prompt_message=f"⚠️  Allow HIGH RISK operation '{args.operation_type}'? ⚠️",
            content_to_display=warning_content
        )
    
    # Continue based on approval status...
```

### Progress Tracking

```python
from rich.progress import Progress

async def long_running_tool(console: RichConsole, args: LongInput) -> LongOutput:
    with Progress() as progress:
        task = progress.add_task("Processing...", total=len(args.items))
        
        results = []
        for i, item in enumerate(args.items):
            result = await process_item(item)
            results.append(result)
            progress.update(task, advance=1)
            
            # Yield control for responsiveness
            if i % 10 == 0:
                await asyncio.sleep(0.01)
        
        return LongOutput(results=results)
```

### Configuration Integration

```python
from qx.core.config_manager import ConfigManager

async def configurable_tool(console: RichConsole, args: ConfigInput) -> ConfigOutput:
    # Access user configuration
    config = ConfigManager(console, None)
    
    # Get tool-specific settings
    tool_config = config.get("tools.my_tool", {})
    default_timeout = tool_config.get("timeout", 30)
    
    # Use configuration in tool logic
    timeout = args.timeout or default_timeout
    # ... rest of tool implementation
```

## Troubleshooting

### Common Issues

1. **Tool not discovered**: Check file naming (`*_plugin.py`) and function naming (`*_tool`)
2. **Import errors**: Ensure all dependencies are properly imported
3. **Pydantic validation errors**: Check model field types and constraints
4. **Approval flow not working**: Verify ApprovalHandler usage and console parameter
5. **Console output issues**: Use `_managed_plugin_print` for thread safety

### Debugging

1. **Use logging** extensively with appropriate levels
2. **Test individual components** before integration
3. **Check plugin discovery** in PluginManager
4. **Verify tool schema generation** in OpenAI format
5. **Monitor console output** for error messages

### Performance Issues

1. **Profile async operations** for bottlenecks
2. **Check for blocking calls** in async functions
3. **Monitor memory usage** for large data processing
4. **Use appropriate timeouts** for external calls
5. **Consider chunking** for large datasets

This comprehensive guide should help you create powerful, secure, and user-friendly tools for the QX system. Remember to follow the established patterns and security practices to ensure your tools integrate seamlessly with the existing system.