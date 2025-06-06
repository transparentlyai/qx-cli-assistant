from typing import List, Tuple, Optional, Any, Dict

from rich.console import Console

from qx.core.user_prompts import get_user_choice_from_options_async, is_approve_all_active


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
            header = f"{operation} (Auto-approved) {parameter_name}: {parameter_value}"
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
        display_texts = [text for _, text, _ in options]

        prompt_choices = ", ".join(display_texts)
        full_prompt_text = f"{prompt_message}\n{prompt_choices}?: "

        chosen_key = await get_user_choice_from_options_async(
            self.console,
            full_prompt_text,
            valid_keys,
            default_choice="n",
        )

        if chosen_key and chosen_key in option_map:
            status = option_map[chosen_key]
            return status, chosen_key
        else:
            self.print_outcome("Operation", "Cancelled.", success=False)
            return "cancelled", None
