from typing import Tuple, Optional, Any

from rich.console import Console

from qx.core.user_prompts import (
    get_user_choice_from_options_async,
    is_approve_all_active,
    _approve_all_lock,
)

# Global agent context for approval handlers
_global_agent_context: Optional[dict] = None

def set_global_agent_context(agent_name: str, agent_color: Optional[str] = None) -> None:
    """Set global agent context for approval handlers."""
    global _global_agent_context
    _global_agent_context = {"name": agent_name, "color": agent_color}

def get_global_agent_context() -> Optional[dict]:
    """Get global agent context."""
    return _global_agent_context

def clear_global_agent_context() -> None:
    """Clear global agent context."""
    global _global_agent_context
    _global_agent_context = None


class ApprovalHandler:
    """
    Handles requests for user approval with a standardized messaging format.
    
    Supports both direct console usage and the new console manager
    for thread-safe concurrent access.
    """

    def __init__(self, console: Console, use_console_manager: bool = True):
        self.console = console
        self.use_console_manager = use_console_manager
        self._console_manager = None
        self._current_agent_name = None
        self._current_agent_color = None
        
        if self.use_console_manager:
            try:
                from qx.core.console_manager import get_console_manager
                self._console_manager = get_console_manager()
            except Exception:
                # Fallback to direct console usage if manager unavailable
                self.use_console_manager = False
    
    def set_agent_context(self, agent_name: str, agent_color: str = None) -> None:
        """Set the current agent context for permission request rendering."""
        self._current_agent_name = agent_name
        self._current_agent_color = agent_color
    
    def clear_agent_context(self) -> None:
        """Clear the current agent context."""
        self._current_agent_name = None
        self._current_agent_color = None

    def print_outcome(self, action: str, outcome: str, success: bool = True):
        """Prints the final outcome of an operation."""
        style = "success" if success else "error"
        
        # Get agent context for BorderedMarkdown styling
        agent_name = self._current_agent_name
        agent_color = self._current_agent_color
        if not agent_name:
            global_context = get_global_agent_context()
            if global_context:
                agent_name = global_context.get("name")
                agent_color = global_context.get("color")
        
        # Use BorderedMarkdown if we have agent context
        if agent_name:
            try:
                from qx.cli.quote_bar_component import BorderedMarkdown, get_agent_color
                from rich.markdown import Markdown
                
                # Format with appropriate colors: green for success, red for failure
                # Use Rich Text instead of Markdown to support Rich markup
                from rich.text import Text
                
                status_icon = "✓" if success else "✗"
                status_color = "dim green" if success else "dim red"
                rich_content = f"[{status_color}]└─ {status_icon} {action} {outcome}[/{status_color}]"
                
                # Use agent color for border
                color = get_agent_color(agent_name, agent_color)
                rich_text = Text.from_markup(rich_content)
                bordered_md = BorderedMarkdown(
                    rich_text,
                    border_style=f"dim {color}",
                    background_color="#080808"
                )
                
                if self.use_console_manager and self._console_manager:
                    self._console_manager.print(bordered_md, console=self.console, markup=True, end="")
                else:
                    self.console.print(bordered_md, markup=True, end="")
                return
            except Exception:
                # Fall through to regular printing if BorderedMarkdown fails
                pass
        
        # Fallback to regular printing
        message = f"  └─ {action} {outcome}"
        if self.use_console_manager and self._console_manager:
            self._console_manager.print(message, style=style, console=self.console)
        else:
            self.console.print(message, style=style)

    async def request_approval(
        self,
        operation: str,
        parameter_name: str,
        parameter_value: str,
        prompt_message: str,
        content_to_display: Optional[Any] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Requests user approval using the standardized format.

        Args:
            operation: The operation being performed (e.g., "Read", "Create file").
            parameter_name: The name of the parameter (e.g., "path", "command").
            parameter_value: The value of the parameter.
            prompt_message: The question to ask the user for approval.
            content_to_display: Optional Rich renderable to show as a preview.

        Returns:
            A tuple of (status, chosen_key).
        """
        if await is_approve_all_active():
            header = f"{operation} (Auto-approved) {parameter_name}: [primary]'{parameter_value}'[/]"
            
            # Use local or global agent context
            agent_name = self._current_agent_name
            agent_color = self._current_agent_color
            if not agent_name:
                global_context = get_global_agent_context()
                if global_context:
                    agent_name = global_context.get("name")
                    agent_color = global_context.get("color")
            
            if agent_name:
                # Use agent quote bar for auto-approved requests
                from qx.cli.quote_bar_component import render_agent_permission_request
                request_text = f"{operation} (Auto-approved)\n\n{parameter_name}: `{parameter_value}`"
                render_agent_permission_request(
                    request_text, 
                    agent_name, 
                    agent_color, 
                    console=self.console,
                    additional_content=None
                )
            else:
                if self.use_console_manager and self._console_manager:
                    self._console_manager.print(header, console=self.console)
                else:
                    self.console.print(header)
            return "session_approved", "a"

        # Format permission request content
        agent_name = self._current_agent_name
        agent_color = self._current_agent_color
        
        # Fall back to global agent context if local context not available
        if not agent_name:
            global_context = get_global_agent_context()
            if global_context:
                agent_name = global_context.get("name")
                agent_color = global_context.get("color")
        
        if agent_name:
            # Use agent quote bar for permission requests
            from qx.cli.quote_bar_component import render_agent_permission_request
            
            request_content = f"{operation}\n\n{parameter_name}: `{parameter_value}`"
            
            render_agent_permission_request(
                request_content, 
                agent_name, 
                agent_color, 
                console=self.console,
                additional_content=content_to_display
            )
            
            # Add empty line after permission request
            if self.use_console_manager and self._console_manager:
                self._console_manager.print("", console=self.console)
            else:
                self.console.print("")
        else:
            # Fallback to standard display
            header = f"{operation}: {parameter_value}"
            if self.use_console_manager and self._console_manager:
                self._console_manager.print(header, console=self.console)
            else:
                self.console.print(header)

            if content_to_display:
                if self.use_console_manager and self._console_manager:
                    self._console_manager.print(content_to_display, console=self.console)
                else:
                    self.console.print(content_to_display)

        options = [
            ("y", "Yes", "approved"),
            ("n", "No", "denied"),
            ("a", "All", "session_approved"),
            ("c", "Cancel", "cancelled"),
        ]

        option_map = {key: status for key, _, status in options}
        valid_keys = [key for key, _, _ in options]

        # Display the colored options above the prompt
        colored_options = []
        for key, text, _ in options:
            colored_option = f"[highlight]{text[0]}[/highlight]{text[1:]}"
            colored_options.append(colored_option)
        
        options_display = " | ".join(colored_options)
        if self.use_console_manager and self._console_manager:
            self._console_manager.print(f"Options: {options_display}", console=self.console)
        else:
            self.console.print(f"Options: {options_display}")

        # Create plain text prompt for input() function
        plain_choices = "/".join([key for key, _, _ in options])
        full_prompt_text = f"{prompt_message} ({plain_choices}): "

        if self.use_console_manager and self._console_manager:
            chosen_key = self._console_manager.request_choice_blocking(
                prompt_text_with_options=full_prompt_text,
                valid_choices=valid_keys,
                console=self.console,
                default_choice=None
            )
        else:
            chosen_key = await get_user_choice_from_options_async(
                self.console,
                full_prompt_text,
                valid_keys,
                default_choice=None,
            )

        if chosen_key and chosen_key in option_map:
            # Handle "All" option to activate session auto-approve
            if chosen_key == "a":
                # Modify the global variable through the module to ensure consistency
                import qx.core.user_prompts as user_prompts
                async with _approve_all_lock:
                    user_prompts._approve_all_active = True
                if self.use_console_manager and self._console_manager:
                    self._console_manager.print(
                        "[info]'Approve All' activated for this session.[/info]",
                        console=self.console
                    )
                else:
                    self.console.print(
                        "[info]'Approve All' activated for this session.[/info]"
                    )

            status = option_map[chosen_key]
            return status, chosen_key
        else:
            self.print_outcome("Operation", "Cancelled.", success=False)
            return "cancelled", None
