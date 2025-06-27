"""
Directive Manager for QX.

This module handles discovery and loading of directives - reusable prompts
that users can invoke with @ syntax (e.g., @worklogger).

Directives are discovered from:
- Built-in: src/qx/directives/
- Project-specific: .Q/directives/
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Directive:
    """Represents a directive with its content and metadata."""
    name: str
    content: str
    source_path: Path
    is_builtin: bool
    
    def __str__(self) -> str:
        return f"@{self.name}"


class DirectiveManager:
    """Manages directive discovery, loading, and caching."""
    
    def __init__(self):
        self._directives: Dict[str, Directive] = {}
        self._builtin_dirs: List[Path] = []
        self._project_dirs: List[Path] = []
        self._initialized = False
        
        # Find built-in directives directory
        try:
            import qx
            qx_root = Path(qx.__file__).parent
            builtin_dir = qx_root / "directives"
            if builtin_dir.exists():
                self._builtin_dirs.append(builtin_dir)
                logger.debug(f"Found built-in directives directory: {builtin_dir}")
        except Exception as e:
            logger.warning(f"Could not locate built-in directives: {e}")
    
    def discover_directives(self, cwd: Optional[str] = None) -> None:
        """
        Discover all available directives from built-in and project directories.
        
        Args:
            cwd: Current working directory for finding project directives
        """
        self._directives.clear()
        
        # Discover built-in directives
        for builtin_dir in self._builtin_dirs:
            self._scan_directory(builtin_dir, is_builtin=True)
        
        # Discover project directives
        if cwd:
            project_dir = Path(cwd) / ".Q" / "directives"
            if project_dir.exists() and project_dir.is_dir():
                self._scan_directory(project_dir, is_builtin=False)
                logger.debug(f"Found project directives directory: {project_dir}")
        
        self._initialized = True
        logger.info(f"Discovered {len(self._directives)} directives")
    
    def _scan_directory(self, directory: Path, is_builtin: bool) -> None:
        """Scan a directory for .md directive files."""
        try:
            for file_path in directory.glob("*.md"):
                if file_path.is_file():
                    directive_name = file_path.stem.lower()
                    
                    # Skip if we already have this directive (project overrides built-in)
                    if directive_name in self._directives and not is_builtin:
                        logger.debug(f"Project directive '{directive_name}' overrides built-in")
                    
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        self._directives[directive_name] = Directive(
                            name=directive_name,
                            content=content,
                            source_path=file_path,
                            is_builtin=is_builtin
                        )
                        logger.debug(f"Loaded directive: @{directive_name} from {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to load directive {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to scan directory {directory}: {e}")
    
    def get_directive(self, name: str) -> Optional[Directive]:
        """
        Get a directive by name (without @ prefix).
        
        Args:
            name: Directive name (e.g., 'worklogger')
            
        Returns:
            Directive object if found, None otherwise
        """
        if not self._initialized:
            self.discover_directives(os.getcwd())
        
        return self._directives.get(name.lower())
    
    def list_directives(self) -> List[Directive]:
        """Get all available directives."""
        if not self._initialized:
            self.discover_directives(os.getcwd())
        
        return sorted(self._directives.values(), key=lambda d: d.name)
    
    def get_directive_names(self) -> List[str]:
        """Get all directive names for autocomplete."""
        if not self._initialized:
            self.discover_directives(os.getcwd())
        
        return sorted(self._directives.keys())
    
    def refresh(self, cwd: Optional[str] = None) -> None:
        """Refresh directive discovery."""
        self.discover_directives(cwd)


# Global instance
_directive_manager: Optional[DirectiveManager] = None


def get_directive_manager() -> DirectiveManager:
    """Get the global directive manager instance."""
    global _directive_manager
    if _directive_manager is None:
        _directive_manager = DirectiveManager()
    return _directive_manager