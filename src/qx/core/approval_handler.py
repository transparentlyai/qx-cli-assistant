import asyncio
from typing import Tuple, Optional, Any

from rich.console import Console

from qx.core.user_prompts import (
    get_user_choice_from_options_async,
    is_approve_all_active,
    _approve_all_active,
    _approve_all_lock,
)


class ApprovalHandler:
    """
    Handles requests for user approval with a standardized messaging format.
    """

    def __init__(self, console: Console):
        self.console = console

    def print_outcome(self, action: str, outcome: str, success: bool = True):
        """Prints the final outcome of an operation."""
        style = "success" if success else "error"
        self.console.print(f"  └─ {action} {outcome}", style=style)

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
            self.console.print(header)
            return "session_approved", "a"

        header = f"{operation}: {parameter_value}"
        self.console.print(header)

        if content_to_display:
            self.console.print(content_to_display)

        options = [
            ("y", "Yes", "approved"),
            ("n", "No", "denied"),
            ("a", "All", "session_approved"),
            ("c", "Cancel", "cancelled"),
        ]

        option_map = {key: status for key, _, status in options}
        valid_keys = [key for key, _, _ in options]
        
        # Color the first letter of each option
        colored_display_texts = []
        for key, text, _ in options:
            colored_text = f"[highlight]{text[0]}[/highlight]{text[1:]}"
            colored_display_texts.append(colored_text)

        prompt_choices = ", ".join(colored_display_texts)
        full_prompt_text = f"{prompt_message} ({prompt_choices}) "

        chosen_key = await get_user_choice_from_options_async(
            self.console,
            full_prompt_text,
            valid_keys,
            default_choice=None,
        )

        if chosen_key and chosen_key in option_map:
            # Handle "All" option to activate session auto-approve
            if chosen_key == "a":
                # Import the module to modify the global variable properly
                import qx.core.user_prompts as user_prompts
                async with _approve_all_lock:
                    user_prompts._approve_all_active = True
                self.console.print("[info]'Approve All' activated for this session.[/info]")
            
            status = option_map[chosen_key]
            return status, chosen_key
        else:
            self.print_outcome("Operation", "Cancelled.", success=False)
            return "cancelled", None
