"""
Utilities for handling command history parsing and formatting.
Supports TUI mode with + prefixed format and timestamps.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


def parse_history_file(history_file: Path) -> List[str]:
    """
    Parse history file and return list of commands.
    Handles both + prefixed format and legacy format.
    
    Args:
        history_file: Path to the history file
        
    Returns:
        List of command strings (multiline commands are joined with \n)
    """
    if not history_file.exists():
        return []
    
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        commands = []
        current_command_parts = []
        idx = 0
        
        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue
            
            if line.startswith("# "):
                # Process any pending command parts
                if current_command_parts:
                    commands.append("\n".join(current_command_parts))
                    current_command_parts = []
                idx += 1
            elif line.startswith("+"):
                # Command line with + prefix
                command_part = line[1:]  # Remove + prefix
                current_command_parts.append(command_part)
                idx += 1
            else:
                # Legacy format without + prefix
                if current_command_parts:
                    commands.append("\n".join(current_command_parts))
                    current_command_parts = []
                commands.append(line)
                idx += 1
        
        # Handle any remaining command parts
        if current_command_parts:
            commands.append("\n".join(current_command_parts))
        
        return commands
        
    except IOError as e:
        logger.error(f"Error reading history file {history_file}: {e}")
        return []


def save_command_to_history(history_file: Path, command: str) -> None:
    """
    Save a command to history file with proper + prefix format and timestamp.
    
    Args:
        history_file: Path to the history file
        command: Command string to save (can be multiline)
    """
    command = command.strip()
    if not command:
        return
    
    try:
        # Ensure parent directory exists
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(history_file, "a", encoding="utf-8") as f:
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            f.write(f"# {timestamp}\n")
            # Add command with + prefix, handling multiline
            for line in command.splitlines():
                f.write(f"+{line}\n")
            f.write("\n")  # Empty line separator
            
    except IOError as e:
        logger.error(f"Error writing to history file {history_file}: {e}")


def parse_history_for_fzf(history_file: Path) -> List[Tuple[str, str]]:
    """
    Parse history file for fzf display, returning (display_string, original_command) tuples.
    
    Args:
        history_file: Path to the history file
        
    Returns:
        List of (display_string, original_command) tuples for fzf
    """
    if not history_file.exists() or history_file.stat().st_size == 0:
        return []
    
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except IOError as e:
        logger.error(f"Error reading history file for fzf: {e}")
        return []
    
    if not lines:
        return []
    
    processed_history_entries = []
    current_command_parts = []
    current_timestamp_str = None
    idx = 0
    
    while idx < len(lines):
        line_with_nl = lines[idx]
        stripped_line = line_with_nl.strip()
        if not stripped_line:
            idx += 1
            continue
        
        if stripped_line.startswith("# "):
            if current_command_parts:
                original_command = "\n".join(current_command_parts)
                fzf_display_command = original_command.replace("\n", " ↵ ")
                formatted_ts_display = " " * 15
                display_string = f"{formatted_ts_display}  {fzf_display_command}"
                processed_history_entries.append((display_string, original_command))
                current_command_parts = []
            current_timestamp_str = stripped_line
            idx += 1
        elif stripped_line.startswith("+"):
            command_part = stripped_line[1:]
            current_command_parts.append(command_part)
            idx += 1
            while idx < len(lines) and lines[idx].strip().startswith("+"):
                current_command_parts.append(lines[idx].strip()[1:])
                idx += 1
            original_command = "\n".join(current_command_parts)
            fzf_display_command = original_command.replace("\n", " ↵ ")
            formatted_ts_display = " " * 15
            if current_timestamp_str:
                ts_content = current_timestamp_str[2:].strip()
                dt_obj = None
                try:
                    dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try:
                        dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            dt_obj = datetime.fromtimestamp(float(ts_content))
                        except ValueError:
                            pass
                if dt_obj:
                    formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
            display_string = f"{formatted_ts_display}  {fzf_display_command}"
            processed_history_entries.append((display_string, original_command))
            current_command_parts = []
            current_timestamp_str = None
        else:
            # Legacy format
            if current_command_parts:
                original_command_pending = "\n".join(current_command_parts)
                fzf_display_command_pending = original_command_pending.replace("\n", " ↵ ")
                ts_placeholder_pending = " " * 15
                display_string_pending = f"{ts_placeholder_pending}  {fzf_display_command_pending}"
                processed_history_entries.append((display_string_pending, original_command_pending))
                current_command_parts = []
            original_command = stripped_line
            fzf_display_command = original_command.replace("\n", " ↵ ")
            formatted_ts_display = " " * 15
            display_string = f"{formatted_ts_display}  {fzf_display_command}"
            processed_history_entries.append((display_string, original_command))
            idx += 1
            current_timestamp_str = None
    
    if current_command_parts:
        original_command = "\n".join(current_command_parts)
        fzf_display_command = original_command.replace("\n", " ↵ ")
        formatted_ts_display = " " * 15
        if current_timestamp_str:
            ts_content = current_timestamp_str[2:].strip()
            dt_obj = None
            try:
                dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        dt_obj = datetime.fromtimestamp(float(ts_content))
                    except ValueError:
                        pass
            if dt_obj:
                formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
        display_string = f"{formatted_ts_display}  {fzf_display_command}"
        processed_history_entries.append((display_string, original_command))
    
    return processed_history_entries