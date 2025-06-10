import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)

# In-memory task storage (tasks are not persisted to files)
_task_storage: Dict[str, Dict[str, Any]] = {}

def _managed_plugin_print(content, **kwargs) -> None:
    """Thread-safe console output helper."""
    try:
        from qx.core.console_manager import get_console_manager
        from qx.cli.console import themed_console
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
    from qx.cli.console import themed_console
    themed_console.print(content, **kwargs)

class TodoManagerInput(BaseModel):
    """Input parameters for the todo manager tool."""
    
    action: str = Field(
        description="Action to perform. Valid actions: 'create' (create new todo), 'list' (list all todos), 'get' (get specific todo), 'update' (update todo properties), 'delete' (delete todo), 'add_tasks' (add tasks to todo), 'update_task' (update task status/content), 'complete_task' (mark task as completed)"
    )
    
    todo_id: Optional[str] = Field(
        default=None,
        description="Todo ID for actions that operate on specific todos (get, update, delete, add_tasks). Required for: get, update, delete, add_tasks, update_task, complete_task"
    )
    
    task_id: Optional[str] = Field(
        default=None,
        description="Task ID for actions that operate on specific tasks (update_task, complete_task). Required for: update_task, complete_task"
    )
    
    title: Optional[str] = Field(
        default=None,
        description="Todo title. Required for 'create' action, optional for 'update' action"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Todo description. Optional for 'create' and 'update' actions"
    )
    
    status: Optional[str] = Field(
        default=None,
        description="Todo status. Valid values: 'pending', 'in_progress', 'completed'. Optional for 'create' (defaults to 'pending') and 'update' actions"
    )
    
    priority: Optional[str] = Field(
        default=None,
        description="Todo priority. Valid values: 'low', 'medium', 'high'. Optional for 'create' (defaults to 'medium') and 'update' actions"
    )
    
    tasks: Optional[List[str]] = Field(
        default=None,
        description="List of task descriptions to add. Used with 'create' action (to create todo with initial tasks) or 'add_tasks' action (to add tasks to existing todo)"
    )
    
    task_content: Optional[str] = Field(
        default=None,
        description="New task content when updating a task. Used with 'update_task' action"
    )
    
    task_status: Optional[str] = Field(
        default=None,
        description="New task status when updating a task. Valid values: 'pending', 'in_progress', 'completed'. Used with 'update_task' action"
    )

class TodoManagerOutput(BaseModel):
    """Output from the todo manager tool."""
    
    success: bool = Field(
        description="Whether the operation was successful"
    )
    
    message: str = Field(
        description="Human-readable message describing the result of the operation"
    )
    
    todo_id: Optional[str] = Field(
        default=None,
        description="ID of the todo that was created or operated on"
    )
    
    task_id: Optional[str] = Field(
        default=None,
        description="ID of the task that was created or operated on"
    )
    
    todos: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of todos returned by 'list' action. Each todo includes its tasks"
    )
    
    todo: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Single todo object returned by 'get' action, including its tasks"
    )
    
    task_ids: Optional[List[str]] = Field(
        default=None,
        description="List of task IDs created when adding multiple tasks"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if the operation failed"
    )

def _get_todos_dir() -> Path:
    """Get the todos directory path, creating it if it doesn't exist."""
    todos_dir = Path.home() / ".config" / "qx" / "todos"
    todos_dir.mkdir(parents=True, exist_ok=True)
    return todos_dir

def _load_todo(todo_id: str) -> Optional[Dict[str, Any]]:
    """Load a todo from JSON file."""
    try:
        todos_dir = _get_todos_dir()
        todo_file = todos_dir / f"{todo_id}.json"
        
        if not todo_file.exists():
            return None
            
        with open(todo_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load todo {todo_id}: {e}")
        return None

def _save_todo(todo: Dict[str, Any]) -> bool:
    """Save a todo to JSON file."""
    try:
        todos_dir = _get_todos_dir()
        todo_file = todos_dir / f"{todo['id']}.json"
        
        todo['updated_at'] = datetime.now().isoformat()
        
        with open(todo_file, 'w') as f:
            json.dump(todo, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save todo {todo['id']}: {e}")
        return False

def _delete_todo_file(todo_id: str) -> bool:
    """Delete a todo JSON file."""
    try:
        todos_dir = _get_todos_dir()
        todo_file = todos_dir / f"{todo_id}.json"
        
        if todo_file.exists():
            todo_file.unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to delete todo file {todo_id}: {e}")
        return False

def _list_all_todos() -> List[Dict[str, Any]]:
    """List all todos from JSON files."""
    try:
        todos_dir = _get_todos_dir()
        todos = []
        
        for todo_file in todos_dir.glob("*.json"):
            try:
                with open(todo_file, 'r') as f:
                    todo = json.load(f)
                    # Add tasks from memory
                    todo['tasks'] = _get_tasks_for_todo(todo['id'])
                    todos.append(todo)
            except Exception as e:
                logger.error(f"Failed to load todo from {todo_file}: {e}")
                continue
        
        # Sort by created_at
        todos.sort(key=lambda x: x.get('created_at', ''))
        return todos
    except Exception as e:
        logger.error(f"Failed to list todos: {e}")
        return []

def _get_tasks_for_todo(todo_id: str) -> List[Dict[str, Any]]:
    """Get all tasks for a specific todo from memory."""
    return [task for task in _task_storage.values() if task.get('todo_id') == todo_id]

def _create_task(todo_id: str, content: str) -> str:
    """Create a new task in memory and return its ID."""
    task_id = str(uuid.uuid4())
    task = {
        'id': task_id,
        'todo_id': todo_id,
        'content': content,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    _task_storage[task_id] = task
    return task_id

def _update_task(task_id: str, content: Optional[str] = None, status: Optional[str] = None) -> bool:
    """Update a task in memory."""
    if task_id not in _task_storage:
        return False
    
    task = _task_storage[task_id]
    if content is not None:
        task['content'] = content
    if status is not None:
        task['status'] = status
    task['updated_at'] = datetime.now().isoformat()
    return True

def _delete_tasks_for_todo(todo_id: str) -> None:
    """Delete all tasks for a specific todo from memory."""
    task_ids_to_delete = [
        task_id for task_id, task in _task_storage.items()
        if task.get('todo_id') == todo_id
    ]
    for task_id in task_ids_to_delete:
        del _task_storage[task_id]

def _display_todo_with_tasks(console: RichConsole, todo: Dict[str, Any]) -> None:
    """Display a nicely formatted todo with its tasks."""
    # Get tasks for this todo
    tasks = _get_tasks_for_todo(todo['id'])
    
    # Create status indicators
    status_colors = {
        'pending': 'yellow',
        'in_progress': 'blue', 
        'completed': 'green'
    }
    
    priority_colors = {
        'low': 'dim',
        'medium': 'white',
        'high': 'bold red'
    }
    
    # Create the main todo header
    status_color = status_colors.get(todo['status'], 'white')
    priority_color = priority_colors.get(todo['priority'], 'white')
    
    header = Text()
    header.append(f"• {todo['title']}", style="bold")
    header.append(f" [{todo['status'].upper()}]", style=f"bold {status_color}")
    header.append(f" (Priority: {todo['priority']})", style=priority_color)
    
    # Create tasks table
    if tasks:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Status", width=3)
        table.add_column("Task")
        
        for i, task in enumerate(tasks, 1):
            status_icon = "✓" if task['status'] == 'completed' else "~" if task['status'] == 'in_progress' else "·"
            task_style = "dim" if task['status'] == 'completed' else "white"
            table.add_row(status_icon, f"{i}. {task['content']}", style=task_style)
    else:
        table = Text("  No tasks yet", style="dim italic")
    
    # Build content
    content_parts = []
    if todo.get('description'):
        content_parts.append(todo['description'])
        content_parts.append("")  # Empty line
    
    # Create a single content string or Rich object
    if isinstance(table, Table):
        if content_parts:
            from rich.console import Group
            content_text = Text("\n".join(content_parts), style="italic")
            content = Group(content_text, table)
        else:
            content = table
    else:
        if content_parts:
            content_parts.append(str(table))
        else:
            content_parts.append(str(table))
        content = Text("\n".join(content_parts))
    
    # Create panel
    panel = Panel(
        content,
        title=header,
        border_style=status_color,
        padding=(0, 1)
    )
    
    # Use thread-safe console output
    _managed_plugin_print(panel)
    # Note: Removed spacing to prevent extra lines between tool messages

async def todo_manager_tool(
    console: RichConsole, 
    args: TodoManagerInput
) -> TodoManagerOutput:
    """
    Manage todos and tasks with persistent storage and in-memory task tracking.
    
    This tool provides comprehensive todo and task management capabilities for LLM agents.
    Todos are persisted as JSON files while tasks are kept in memory for performance.
    
    Usage Examples:
        
        # Create a new todo
        action="create", title="Implement user authentication", description="Add login/logout functionality"
        
        # Create a todo with initial tasks
        action="create", title="Build API", tasks=["Design endpoints", "Implement routes", "Add tests"]
        
        # List all todos (shows todos with their tasks)
        action="list"
        
        # Get specific todo details
        action="get", todo_id="12345"
        
        # Update todo properties
        action="update", todo_id="12345", status="in_progress", priority="high"
        
        # Add tasks to existing todo
        action="add_tasks", todo_id="12345", tasks=["Review code", "Deploy to staging"]
        
        # Update a specific task
        action="update_task", todo_id="12345", task_id="67890", task_content="Updated task description", task_status="completed"
        
        # Mark a task as completed (shortcut)
        action="complete_task", todo_id="12345", task_id="67890"
        
        # Delete a todo (removes todo and all its tasks)
        action="delete", todo_id="12345"
    
    Todo Statuses: pending, in_progress, completed
    Todo Priorities: low, medium, high
    Task Statuses: pending, in_progress, completed
    
    Data Persistence:
        - Todos: Stored as JSON files in ~/.config/qx/todos/
        - Tasks: Kept in memory for performance (recreated on restart)
        - Each todo has a unique UUID as its filename
    
    Args:
        console: Rich console for output (automatically provided)
        args: TodoManagerInput with action and relevant parameters
        
    Returns:
        TodoManagerOutput: Operation result with success status, messages, and data
    """
    try:
        action = args.action.lower()
        
        if action == "create":
            if not args.title:
                return TodoManagerOutput(
                    success=False,
                    message="Title is required for creating a todo",
                    error="Missing required parameter: title"
                )
            
            # Create new todo
            todo_id = str(uuid.uuid4())
            todo = {
                'id': todo_id,
                'title': args.title,
                'description': args.description or "",
                'status': args.status or 'pending',
                'priority': args.priority or 'medium',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Save todo to file
            if not _save_todo(todo):
                return TodoManagerOutput(
                    success=False,
                    message="Failed to save todo to file",
                    error="File system error"
                )
            
            # Create initial tasks if provided
            task_ids = []
            if args.tasks:
                for task_content in args.tasks:
                    task_id = _create_task(todo_id, task_content)
                    task_ids.append(task_id)
            
            _managed_plugin_print(f"[green]+ Created todo '{args.title}' with ID: {todo_id}[/green]")
            if task_ids:
                _managed_plugin_print(f"[blue]+ Added {len(task_ids)} initial tasks[/blue]")
            
            # Display the formatted todo
            todo['tasks'] = _get_tasks_for_todo(todo_id)
            _display_todo_with_tasks(console, todo)
            
            return TodoManagerOutput(
                success=True,
                message=f"Created todo '{args.title}' with {len(task_ids)} tasks",
                todo_id=todo_id,
                task_ids=task_ids if task_ids else None
            )
        
        elif action == "list":
            todos = _list_all_todos()
            _managed_plugin_print(f"[blue]Found {len(todos)} todos[/blue]")
            
            return TodoManagerOutput(
                success=True,
                message=f"Listed {len(todos)} todos",
                todos=todos
            )
        
        elif action == "get":
            if not args.todo_id:
                return TodoManagerOutput(
                    success=False,
                    message="Todo ID is required for getting a todo",
                    error="Missing required parameter: todo_id"
                )
            
            todo = _load_todo(args.todo_id)
            if not todo:
                return TodoManagerOutput(
                    success=False,
                    message=f"Todo with ID {args.todo_id} not found",
                    error="Todo not found"
                )
            
            # Add tasks from memory
            todo['tasks'] = _get_tasks_for_todo(args.todo_id)
            
            _managed_plugin_print(f"[blue]Retrieved todo: {todo['title']}[/blue]")
            
            return TodoManagerOutput(
                success=True,
                message=f"Retrieved todo '{todo['title']}'",
                todo_id=args.todo_id,
                todo=todo
            )
        
        elif action == "update":
            if not args.todo_id:
                return TodoManagerOutput(
                    success=False,
                    message="Todo ID is required for updating a todo",
                    error="Missing required parameter: todo_id"
                )
            
            todo = _load_todo(args.todo_id)
            if not todo:
                return TodoManagerOutput(
                    success=False,
                    message=f"Todo with ID {args.todo_id} not found",
                    error="Todo not found"
                )
            
            # Update fields if provided
            updated_fields = []
            if args.title is not None:
                todo['title'] = args.title
                updated_fields.append('title')
            if args.description is not None:
                todo['description'] = args.description
                updated_fields.append('description')
            if args.status is not None:
                todo['status'] = args.status
                updated_fields.append('status')
            if args.priority is not None:
                todo['priority'] = args.priority
                updated_fields.append('priority')
            
            if not updated_fields:
                return TodoManagerOutput(
                    success=False,
                    message="No fields provided to update",
                    error="No update parameters provided"
                )
            
            # Save updated todo
            if not _save_todo(todo):
                return TodoManagerOutput(
                    success=False,
                    message="Failed to save updated todo",
                    error="File system error"
                )
            
            _managed_plugin_print(f"[green]Updated todo '{todo['title']}' fields: {', '.join(updated_fields)}[/green]")
            
            return TodoManagerOutput(
                success=True,
                message=f"Updated todo '{todo['title']}' ({', '.join(updated_fields)})",
                todo_id=args.todo_id
            )
        
        elif action == "delete":
            if not args.todo_id:
                return TodoManagerOutput(
                    success=False,
                    message="Todo ID is required for deleting a todo",
                    error="Missing required parameter: todo_id"
                )
            
            todo = _load_todo(args.todo_id)
            if not todo:
                return TodoManagerOutput(
                    success=False,
                    message=f"Todo with ID {args.todo_id} not found",
                    error="Todo not found"
                )
            
            # Delete tasks from memory
            _delete_tasks_for_todo(args.todo_id)
            
            # Delete todo file
            if not _delete_todo_file(args.todo_id):
                return TodoManagerOutput(
                    success=False,
                    message="Failed to delete todo file",
                    error="File system error"
                )
            
            _managed_plugin_print(f"[red]Deleted todo '{todo['title']}' and all its tasks[/red]")
            
            return TodoManagerOutput(
                success=True,
                message=f"Deleted todo '{todo['title']}' and all its tasks",
                todo_id=args.todo_id
            )
        
        elif action == "add_tasks":
            if not args.todo_id:
                return TodoManagerOutput(
                    success=False,
                    message="Todo ID is required for adding tasks",
                    error="Missing required parameter: todo_id"
                )
            
            if not args.tasks:
                return TodoManagerOutput(
                    success=False,
                    message="Tasks list is required for adding tasks",
                    error="Missing required parameter: tasks"
                )
            
            # Verify todo exists
            todo = _load_todo(args.todo_id)
            if not todo:
                return TodoManagerOutput(
                    success=False,
                    message=f"Todo with ID {args.todo_id} not found",
                    error="Todo not found"
                )
            
            # Create tasks
            task_ids = []
            for task_content in args.tasks:
                task_id = _create_task(args.todo_id, task_content)
                task_ids.append(task_id)
            
            _managed_plugin_print(f"[blue]+ Added {len(task_ids)} tasks to todo '{todo['title']}'[/blue]")
            
            # Display the updated todo
            todo['tasks'] = _get_tasks_for_todo(args.todo_id)
            _display_todo_with_tasks(console, todo)
            
            return TodoManagerOutput(
                success=True,
                message=f"Added {len(task_ids)} tasks to todo '{todo['title']}'",
                todo_id=args.todo_id,
                task_ids=task_ids
            )
        
        elif action == "update_task":
            if not args.todo_id or not args.task_id:
                return TodoManagerOutput(
                    success=False,
                    message="Both todo_id and task_id are required for updating a task",
                    error="Missing required parameters: todo_id and/or task_id"
                )
            
            # Verify todo exists
            todo = _load_todo(args.todo_id)
            if not todo:
                return TodoManagerOutput(
                    success=False,
                    message=f"Todo with ID {args.todo_id} not found",
                    error="Todo not found"
                )
            
            # Verify task exists and belongs to todo
            if args.task_id not in _task_storage:
                return TodoManagerOutput(
                    success=False,
                    message=f"Task with ID {args.task_id} not found",
                    error="Task not found"
                )
            
            task = _task_storage[args.task_id]
            if task['todo_id'] != args.todo_id:
                return TodoManagerOutput(
                    success=False,
                    message="Task does not belong to the specified todo",
                    error="Task-todo mismatch"
                )
            
            # Update task
            updated_fields = []
            if args.task_content is not None:
                updated_fields.append('content')
            if args.task_status is not None:
                updated_fields.append('status')
            
            if not updated_fields:
                return TodoManagerOutput(
                    success=False,
                    message="No task fields provided to update",
                    error="No update parameters provided"
                )
            
            if not _update_task(args.task_id, args.task_content, args.task_status):
                return TodoManagerOutput(
                    success=False,
                    message="Failed to update task",
                    error="Task update failed"
                )
            
            _managed_plugin_print(f"[green]Updated task in '{todo['title']}' ({', '.join(updated_fields)})[/green]")
            
            return TodoManagerOutput(
                success=True,
                message=f"Updated task in '{todo['title']}' ({', '.join(updated_fields)})",
                todo_id=args.todo_id,
                task_id=args.task_id
            )
        
        elif action == "complete_task":
            if not args.todo_id or not args.task_id:
                return TodoManagerOutput(
                    success=False,
                    message="Both todo_id and task_id are required for completing a task",
                    error="Missing required parameters: todo_id and/or task_id"
                )
            
            # Verify todo exists
            todo = _load_todo(args.todo_id)
            if not todo:
                return TodoManagerOutput(
                    success=False,
                    message=f"Todo with ID {args.todo_id} not found",
                    error="Todo not found"
                )
            
            # Verify task exists and belongs to todo
            if args.task_id not in _task_storage:
                return TodoManagerOutput(
                    success=False,
                    message=f"Task with ID {args.task_id} not found",
                    error="Task not found"
                )
            
            task = _task_storage[args.task_id]
            if task['todo_id'] != args.todo_id:
                return TodoManagerOutput(
                    success=False,
                    message="Task does not belong to the specified todo",
                    error="Task-todo mismatch"
                )
            
            # Mark task as completed
            if not _update_task(args.task_id, status='completed'):
                return TodoManagerOutput(
                    success=False,
                    message="Failed to complete task",
                    error="Task update failed"
                )
            
            _managed_plugin_print(f"[green]✓ Completed task '{task['content']}' in '{todo['title']}'[/green]")
            
            # Display the updated todo
            todo['tasks'] = _get_tasks_for_todo(args.todo_id)
            _display_todo_with_tasks(console, todo)
            
            return TodoManagerOutput(
                success=True,
                message=f"Completed task '{task['content']}' in '{todo['title']}'",
                todo_id=args.todo_id,
                task_id=args.task_id
            )
        
        else:
            return TodoManagerOutput(
                success=False,
                message=f"Unknown action: {action}",
                error=f"Invalid action '{action}'. Valid actions: create, list, get, update, delete, add_tasks, update_task, complete_task"
            )
    
    except Exception as e:
        logger.error(f"Todo manager tool failed: {e}", exc_info=True)
        return TodoManagerOutput(
            success=False,
            message="Tool execution failed",
            error=f"Unexpected error: {e}"
        )