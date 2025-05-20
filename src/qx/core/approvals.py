# src/qx/core/approvals.py
# This module previously contained the ApprovalManager.
# Its responsibilities have been moved to:
# - src/qx/core/user_prompts.py (for the generic request_confirmation utility)
# - Individual plugins in src/qx/plugins/ (for specific approval logic,
#   content preview generation, and prohibited/allowed command checks).

# This file can be removed in a future cleanup if no other core approval-related
# utilities are envisioned to reside here. For now, it's kept as a placeholder
# to signify the architectural change.

import logging

logger = logging.getLogger(__name__)

logger.info(
    "ApprovalManager has been refactored. See src/qx/core/user_prompts.py "
    "and individual plugins for new approval mechanisms."
)

# To prevent accidental imports of the old ApprovalManager if not all
# references are updated immediately, we can raise an AttributeError or print a warning.
# For now, just logging is sufficient during the transition.

# class ApprovalManager:
#     pass # Old class removed
