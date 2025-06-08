from typing import Tuple, Optional, Any

from rich.console import Console

from qx.core.user_prompts import (
    get_user_choice_from_options_async,
    is_approve_all_active,
    _approve_all_lock,
)


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
        
        if self.use_console_manager:
            try:
                from qx.core.console_manager import get_console_manager
                self._console_manager = get_console_manager()
            except Exception:
                # Fallback to direct console usage if manager unavailable
                self.use_console_manager = False

    def print_outcome(self, action: str, outcome: str, success: bool = True):
        """Prints the final outcome of an operation."""
        style = "success" if success else "error"
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
            if self.use_console_manager and self._console_manager:
                self._console_manager.print(header, console=self.console)
            else:
                self.console.print(header)
            return "session_approved", "a"

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

        # Color the first letter of each option
        colored_display_texts = []
        for key, text, _ in options:
            colored_text = f"[highlight]{text[0]}[/highlight]{text[1:]}"
            colored_display_texts.append(colored_text)

        prompt_choices = ", ".join(colored_display_texts)
        full_prompt_text = f"{prompt_message} ({prompt_choices}) "

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
