"""
Workflow manager to handle the transition between old and new implementations.

This module provides a unified interface that can switch between:
- Original langgraph_supervisor.py (complex manual implementation)
- New langgraph_supervisor_v2.py (using langgraph-supervisor library)
"""

import logging
import os
from typing import Optional

from qx.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Environment variable to control which implementation to use
USE_V2_WORKFLOW = os.getenv("QX_USE_V2_WORKFLOW", "false").lower() == "true"


class WorkflowManager:
    """Manages the workflow implementation selection and execution."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._workflow_instance = None
        self._implementation = "v2" if USE_V2_WORKFLOW else "v1"
        
        logger.info(f"WorkflowManager using implementation: {self._implementation}")
        
    async def get_workflow(self):
        """Get the appropriate workflow implementation."""
        if self._workflow_instance is None:
            if self._implementation == "v2":
                # Use new simplified implementation
                from qx.core.langgraph_supervisor_v2 import get_unified_workflow_v2
                self._workflow_instance = get_unified_workflow_v2(self.config_manager)
                logger.info("Loaded V2 workflow (langgraph-supervisor library)")
            else:
                # Use original implementation
                from qx.core.langgraph_supervisor import get_unified_workflow
                self._workflow_instance = get_unified_workflow(self.config_manager)
                logger.info("Loaded V1 workflow (manual implementation)")
                
        return self._workflow_instance
    
    async def process_in_team_mode(self, user_input: str = "") -> Optional[str]:
        """Process input in team mode using the appropriate workflow."""
        workflow = await self.get_workflow()
        
        if self._implementation == "v2":
            # V2 implementation
            if user_input:
                return await workflow.process_input(user_input)
            else:
                # Start continuous mode
                await workflow.start_continuous_workflow()
                return None
        else:
            # V1 implementation
            return await workflow.process_with_unified_workflow(user_input)
            
    def should_use_workflow(self) -> bool:
        """Check if workflow should be used (team mode is active)."""
        from qx.core.team_mode_manager import get_team_mode_manager
        team_mode_manager = get_team_mode_manager()
        return team_mode_manager.is_team_mode_enabled()


# Singleton instance
_workflow_manager_instance: Optional[WorkflowManager] = None


def get_workflow_manager(config_manager: ConfigManager) -> WorkflowManager:
    """Get or create the workflow manager instance."""
    global _workflow_manager_instance
    
    if _workflow_manager_instance is None:
        _workflow_manager_instance = WorkflowManager(config_manager)
        
    return _workflow_manager_instance