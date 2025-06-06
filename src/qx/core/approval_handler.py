from typing import List, Tuple, Optional, Any, Dict

from rich.console import Console

# This function will be implemented in src/qx/core/user_prompts.py
from qx.core.user_prompts import get_user_choice_from_options_async


class ApprovalHandler:
    """
    Handles requests for user approval with dynamic options.
    Relies on `get_user_choice_from_options_async` from qx.core.user_prompts
    to perform the actual interactive terminal input.
    """

    def __init__(self, console: Console):
        self.console = console

    async def request_approval(
        self,
        prompt_message: str,
        options: List[
            Tuple[str, str, str]
        ],  # (key_char, display_text, status_to_return)
        content_to_display: Optional[Any] = None,
        default_cancel_option: bool = True,
    ) -> Tuple[str, Optional[str]]:  # (status_returned, chosen_key_or_None)
        """
        Requests user approval by displaying a prompt and dynamic options.

        Args:
            prompt_message: The main message/question for the user.
            options: A list of tuples, each defining an option:
                     (key_char, display_text, status_to_return_if_chosen).
                     Example: [('a', 'Approve', 'approved'), ('d', 'Deny', 'denied')]
            content_to_display: Optional Rich renderable to display before the prompt.
            default_cancel_option: If True, automatically adds a ('c', 'Cancel', 'cancelled')
                                     option if 'c' is not already defined.

        Returns:
            A tuple: (status_to_return_if_chosen, chosen_key).
            The 'status_to_return_if_chosen' comes from the 'options' list.
            'chosen_key' is the character input by the user.
            If the input mechanism indicates cancellation (e.g., user presses Esc or Ctrl+C),
            it should return ("cancelled", None) or similar, based on how
            `get_user_choice_from_options_async` handles it.
        """
        if content_to_display:
            self.console.print(content_to_display)

        self.console.print(f"[#6A5ACD]{prompt_message}[/]")  # Lavender color for prompt

        current_options = list(options)  # Make a mutable copy
        option_map: Dict[
            str, Tuple[str, str]
        ] = {}  # key_char -> (display_text, status_to_return)
        valid_key_chars: List[str] = []

        # Prepare option map and check for default cancel
        defined_keys = {opt[0].lower() for opt in current_options}

        if default_cancel_option and "c" not in defined_keys:
            current_options.append(("c", "Cancel", "cancelled"))
            # defined_keys.add("c") # No longer needed as we build valid_key_chars directly

        display_parts = []
        for key, text, status_val in current_options:
            display_parts.append(f"([bold cyan]{key}[/]){text}")
            option_map[key.lower()] = (text, status_val)
            valid_key_chars.append(key.lower())

        options_prompt_text = " / ".join(display_parts) + ": "

        # Call the actual interactive input function
        chosen_key_lower = await get_user_choice_from_options_async(
            self.console,
            options_prompt_text, # The string like "([a])Approve / ([d])Deny: "
            valid_key_chars      # List of valid characters like ['a', 'd', 'c']
        )

        if chosen_key_lower and chosen_key_lower in option_map:
            _, status_to_return = option_map[chosen_key_lower]
            # The get_user_choice_from_options_async function should handle printing the chosen option if desired.
            # self.console.print(f"User chose: {chosen_key_lower} -> {status_to_return}") # Optional debug
            return status_to_return, chosen_key_lower
        else:
            # This case implies cancellation or an issue within get_user_choice_from_options_async
            # if it returns None or an unexpected value not in option_map.
            # Assuming get_user_choice_from_options_async returns None for explicit cancellation.
            self.console.print("[yellow]Operation cancelled by user or invalid input.[/]")
            return "cancelled", None
