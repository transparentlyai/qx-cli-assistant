"""
Team mode state management for qx.

This module manages the team mode enable/disable state with persistent storage
at both project and user levels.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TeamModeManager:
    """Manages team mode state with persistence at project and user levels."""
    
    def __init__(self):
        self._cached_state: Optional[bool] = None
        
    def _get_project_config_path(self) -> Path:
        """Get the project-specific team mode config path."""
        project_path = Path.cwd() / ".Q" / "config" / "team-config.json"
        project_path.parent.mkdir(parents=True, exist_ok=True)
        return project_path
        
    def _get_user_config_path(self) -> Path:
        """Get the user-level team mode config path."""
        user_path = Path.home() / ".config" / "qx" / "team-config.json"
        user_path.parent.mkdir(parents=True, exist_ok=True)
        return user_path
        
    def _load_config_from_file(self, config_path: Path) -> Optional[bool]:
        """Load team mode state from a config file."""
        if not config_path.exists():
            return None
            
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return data.get('team_mode_enabled', None)
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.warning(f"Failed to load team mode config from {config_path}: {e}")
            return None
            
    def _save_config_to_file(self, config_path: Path, enabled: bool) -> bool:
        """Save team mode state to a config file."""
        try:
            config_data = {
                'team_mode_enabled': enabled,
                'version': '1.0'
            }
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save team mode config to {config_path}: {e}")
            return False
            
    def is_team_mode_enabled(self) -> bool:
        """
        Check if team mode is enabled.
        
        Priority order:
        1. Project-specific setting (.Q/team-config.json)
        2. User-level setting (~/.config/qx/team-config.json)  
        3. Default: False
        """
        if self._cached_state is not None:
            return self._cached_state
            
        # Check project-specific setting first (highest priority)
        project_state = self._load_config_from_file(self._get_project_config_path())
        if project_state is not None:
            self._cached_state = project_state
            return project_state
            
        # Check user-level setting
        user_state = self._load_config_from_file(self._get_user_config_path())
        if user_state is not None:
            self._cached_state = user_state
            return user_state
            
        # Default to disabled
        self._cached_state = False
        return False
        
    def set_team_mode_enabled(self, enabled: bool, project_level: bool = True) -> bool:
        """
        Set team mode enabled/disabled state.
        
        Args:
            enabled: Whether to enable team mode
            project_level: If True, save to project config; if False, save to user config
            
        Returns:
            True if successfully saved, False otherwise
        """
        config_path = self._get_project_config_path() if project_level else self._get_user_config_path()
        
        success = self._save_config_to_file(config_path, enabled)
        if success:
            self._cached_state = enabled
            logger.info(f"Team mode {'enabled' if enabled else 'disabled'} at {'project' if project_level else 'user'} level")
        
        return success
        
    def toggle_team_mode(self, project_level: bool = True) -> bool:
        """
        Toggle team mode state.
        
        Args:
            project_level: If True, save to project config; if False, save to user config
            
        Returns:
            New team mode state
        """
        current_state = self.is_team_mode_enabled()
        new_state = not current_state
        
        self.set_team_mode_enabled(new_state, project_level)
        return new_state
        
    def clear_cache(self):
        """Clear cached state to force reload from config files."""
        self._cached_state = None
        
    def get_config_source(self) -> str:
        """Get description of where the current team mode setting comes from."""
        project_state = self._load_config_from_file(self._get_project_config_path())
        if project_state is not None:
            return "project (.Q/config/team-config.json)"
            
        user_state = self._load_config_from_file(self._get_user_config_path())
        if user_state is not None:
            return "user (~/.config/qx/team-config.json)"
            
        return "default (team mode disabled)"


# Global team mode manager instance
_team_mode_manager: Optional[TeamModeManager] = None


def get_team_mode_manager() -> TeamModeManager:
    """Get the global team mode manager instance."""
    global _team_mode_manager
    if _team_mode_manager is None:
        _team_mode_manager = TeamModeManager()
    return _team_mode_manager