#!/usr/bin/env python3
"""Simple test to check workflow state."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Just check basic setup
from qx.core.team_mode_manager import get_team_mode_manager

print("Team mode:", get_team_mode_manager().is_team_mode_enabled())
print("Test complete")