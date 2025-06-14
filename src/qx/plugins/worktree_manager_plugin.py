# src/qx/plugins/worktree_manager_plugin.py
import logging
import re
import asyncio
import subprocess
from typing import Optional, List
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.workflow_approval import create_workflow_aware_approval_handler
from qx.cli.console import themed_console

logger = logging.getLogger(__name__)

class CommandOutput(BaseModel):
    stdout: str
    stderr: str
    return_code: int

class Worktree(BaseModel):
    """Represents a single Git worktree."""
    path: str = Field(description="The absolute path to the worktree.")
    head: str = Field(description="The HEAD commit hash of the worktree.")
    branch: Optional[str] = Field(default=None, description="The branch checked out in the worktree, if any.")

class WorktreeManagerInput(BaseModel):
    """Input parameters for the worktree manager tool."""
    action: str = Field(description="Action to perform: 'list', 'create', or 'remove'.")
    path: Optional[str] = Field(default=None, description="Path for the new worktree (for 'create') or the worktree to remove (for 'remove'.")
    branch: Optional[str] = Field(default=None, description="Branch to check out in the new worktree. Defaults to the current branch if not specified.")
    force: bool = Field(default=False, description="Force removal of the worktree, even if it has uncommitted changes.")

class WorktreeManagerOutput(BaseModel):
    """Output from the worktree manager tool."""
    success: bool = Field(description="Whether the operation was successful.")
    worktrees: Optional[List[Worktree]] = Field(default=None, description="List of worktrees for the 'list' action.")
    output: Optional[str] = Field(default=None, description="Raw output from the git command.")
    error: Optional[str] = Field(default=None, description="Error message if the operation failed.")

async def _run_git_command(command: str) -> CommandOutput:
    """Helper to run a git command."""
    def run_sync_command():
        process = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        return process.stdout, process.stderr, process.returncode

    stdout, stderr, return_code = await asyncio.to_thread(run_sync_command)
    return CommandOutput(
        stdout=stdout.strip() if stdout else "",
        stderr=stderr.strip() if stderr else "",
        return_code=return_code
    )

def _parse_worktree_list(output: str) -> List[Worktree]:
    """Parses the output of 'git worktree list --porcelain'รูปแบบ."""
    worktrees: List[Worktree] = []
    if not output:
        return worktrees
    records = output.strip().split('\n\n')
    for record in records:
        lines = record.strip().split('\n')
        data = {}
        for line in lines:
            if line.startswith('worktree '):
                data['path'] = line[len('worktree '):]
            elif line.startswith('HEAD '):
                data['head'] = line[len('HEAD '):]
            elif line.startswith('branch '):
                data['branch'] = line[len('branch '):].replace('refs/heads/', '')
        if 'path' in data and 'head' in data:
            worktrees.append(Worktree(**data))
    return worktrees

async def worktree_manager_tool(
    console: RichConsole,
    args: WorktreeManagerInput
) -> WorktreeManagerOutput:
    """
    Manages Git worktrees for the project.

    This tool allows you to list, create, and remove Git worktrees.
    It requires user approval for creating and removing worktrees.
    """
    approval_handler = await create_workflow_aware_approval_handler(themed_console)
    
    if args.action == "list":
        command = "git worktree list --porcelain"
        result = await _run_git_command(command)
        
        if result.return_code != 0:
            return WorktreeManagerOutput(success=False, error=result.stderr or "Failed to list worktrees.")
        
        worktrees = _parse_worktree_list(result.stdout)
        return WorktreeManagerOutput(success=True, worktrees=worktrees, output=result.stdout)

    elif args.action == "create":
        if not args.path:
            return WorktreeManagerOutput(success=False, error="The 'path' parameter is required for the 'create' action.")

        if not re.match(r'^[\w\-\_\./]+$', args.path):
            return WorktreeManagerOutput(success=False, error=f"Invalid path specified: {args.path}")
        
        if args.branch and not re.match(r'^[\w\-\_\./]+$', args.branch):
             return WorktreeManagerOutput(success=False, error=f"Invalid branch name specified: {args.branch}")

        command = f"git worktree add {args.path}"
        if args.branch:
            command += f" {args.branch}"
            
        status, _ = await approval_handler.request_approval(
            operation="Create Git Worktree",
            parameter_name="command",
            parameter_value=command,
            prompt_message=f"Allow QX to create a new Git worktree with command: '{command}'?"
        )
        
        if status not in ["approved", "session_approved"]:
            approval_handler.print_outcome("Create Worktree", "Denied by user.", success=False)
            return WorktreeManagerOutput(success=False, error="Operation denied by user.")

        result = await _run_git_command(command)
        
        if result.return_code != 0:
            approval_handler.print_outcome("Create Worktree", f"Failed: {result.stderr}", success=False)
            return WorktreeManagerOutput(success=False, error=result.stderr, output=result.stdout)
        
        approval_handler.print_outcome("Create Worktree", "Completed successfully.", success=True)
        return WorktreeManagerOutput(success=True, output=result.stdout)

    elif args.action == "remove":
        if not args.path:
            return WorktreeManagerOutput(success=False, error="The 'path' parameter is required for the 'remove' action.")

        if not re.match(r'^[\w\-\_\./]+$', args.path):
            return WorktreeManagerOutput(success=False, error=f"Invalid path specified: {args.path}")

        command = f"git worktree remove {args.path}"
        if args.force:
            command += " --force"

        status, _ = await approval_handler.request_approval(
            operation="Remove Git Worktree",
            parameter_name="command",
            parameter_value=command,
            prompt_message=f"Allow QX to remove the Git worktree with command: '{command}'?"
        )

        if status not in ["approved", "session_approved"]:
            approval_handler.print_outcome("Remove Worktree", "Denied by user.", success=False)
            return WorktreeManagerOutput(success=False, error="Operation denied by user.")

        result = await _run_git_command(command)

        if result.return_code != 0:
            approval_handler.print_outcome("Remove Worktree", f"Failed: {result.stderr}", success=False)
            return WorktreeManagerOutput(success=False, error=result.stderr, output=result.stdout)

        approval_handler.print_outcome("Remove Worktree", "Completed successfully.", success=True)
        return WorktreeManagerOutput(success=True, output=result.stdout)

    else:
        return WorktreeManagerOutput(success=False, error=f"Invalid action '{args.action}'. Valid actions are 'list', 'create', 'remove'.")
