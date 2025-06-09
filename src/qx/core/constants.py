# qx/core/constants.py

# Default model name if not specified by the user
# Using LiteLLM format for OpenRouter
DEFAULT_MODEL = "openrouter/anthropic/claude-3.5-sonnet"

# Default tree ignore patterns
DEFAULT_TREE_IGNORE_PATTERNS = [
    ".git",
    ".venv",
    "venv",
    ".env",
    "env",
    "node_modules",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    ".DS_Store",
    "build",
    "dist",
    "target",
    ".pytest_cache",
    ".mypy_cache",
    ".hypothesis",
    ".tox",
    "*.log",
    "*.tmp",
    "*.swp",
    "*.swo",
    ".idea",
    ".vscode",
    "coverage_reports",
    "htmlcov",
    ".coverage",
    "package-lock.json",
    "yarn.lock",
    "yarn-error.log",
    "npm-debug.log",
    "*.class",
    "*.jar",
    "*.war",
    "*.ear",
    ".settings",
    ".classpath",
    ".project",
    # R-specific patterns
    ".Rhistory",
    ".RData",
    "*.Rproj",
    ".Ruserdata",  # Simpler form of .Ruserdata/
    "renv",  # Simpler form of renv/
]

DEFAULT_PROHIBITED_COMMANDS = [
    "sudo *",  # General privilege escalation
    "su *",  # General privilege escalation
    "chmod 777 *",  # Excessive permissions
    "chmod -R 777 *",  # Recursive excessive permissions
    "rm -rf /*",  # Deleting root filesystem
    "dd if=/dev/zero of=/dev/*",  # Overwriting block devices
    "> /dev/sda",  # Overwriting specific block device (example)
    "mkfs.*",  # Formatting filesystems
    ":(){:|:&};:",  # Fork bomb (resource exhaustion)
    "mv /* /dev/null",  # Moving root filesystem contents to null
    "wget * | bash",  # Downloading and executing scripts
    "curl * | bash",  # Downloading and executing scripts
    "wget * | sh",  # Downloading and executing scripts
    "curl * | sh",  # Downloading and executing scripts
    "*(){ :;};*",  # Shellshock vulnerability pattern
    "echo * > /etc/passwd",  # Overwriting password file
    "echo * > /etc/shadow",  # Overwriting shadow password file
    "rm -rf ~",  # Deleting user's home directory
    "rm -rf .",  # Deleting current directory (dangerous if in critical path)
    "find / -delete",  # Find and delete everything from root
    "find . -delete",  # Find and delete everything from current dir
    "shred * /dev/*",  # Securely wiping block devices
    "wipe /dev/*",  # Wiping block devices
    "fdisk /dev/*",  # Disk partitioning tool (interactive)
    "parted /dev/*",  # Disk partitioning tool (interactive/scriptable)
    "gparted /dev/*",  # GUI Disk partitioning tool (can be scripted)
    "userdel root",  # Attempting to delete root user
    "groupdel root",  # Attempting to delete root group
    "passwd -d root",  # Removing root password (security risk)
    "passwd -l root",  # Locking root account
    "chown root* /*",  # Changing ownership of root files (potential breakage)
    "chown -R * /*",  # Recursively changing ownership from root
    "chattr -i *",  # Removing immutable flag (could allow modification of protected files)
    "chattr +i /*",  # Making critical files immutable (could break updates/recovery)
    "reboot",  # System reboot
    "shutdown *",  # System shutdown/reboot/halt
    "halt",  # Halting the system
    "poweroff",  # Powering off the system
    "init 0",  # Halting the system (runlevel)
    "init 6",  # Rebooting the system (runlevel)
    "iptables -F",  # Flushing all firewall rules
    "iptables -X",  # Deleting all non-default firewall chains
    "iptables -P INPUT DROP",  # Setting default input policy to DROP (can lock out)
    "iptables -P FORWARD DROP",  # Setting default forward policy to DROP
    "iptables -P OUTPUT DROP",  # Setting default output policy to DROP (can break connectivity)
    "ufw disable",  # Disabling Uncomplicated Firewall
    "systemctl stop firewalld",  # Stopping firewalld service
    "systemctl disable firewalld",  # Disabling firewalld service
    "insmod *",  # Inserting kernel modules
]

DEFAULT_APPROVED_COMMANDS = [
    "ls",  # List directory contents (no args)
    "ls *",  # List directory contents (with args)
    "cd",  # Change to home directory (no args)
    "cd *",  # Change directory (with args)
    "pwd",  # Print working directory
    "echo",  # Display empty line (no args)
    "echo *",  # Display text (with args)
    "cat",  # Wait for stdin (no args)
    "cat *",  # Concatenate and display files
    "head",  # Wait for stdin (no args)
    "head *",  # Display first part of files
    "tail",  # Wait for stdin (no args)
    "tail *",  # Display last part of files
    "grep",  # Wait for stdin (no args)
    "grep *",  # Search text using patterns
    "find",  # Find in current directory (no args)
    "find *",  # Search for files
    "mkdir",  # Error but harmless (no args)
    "mkdir *",  # Create directories
    "touch",  # Error but harmless (no args)
    "touch *",  # Change file timestamps / create empty files
    "cp",  # Error but harmless (no args)
    "cp *",  # Copy files and directories
    "mv",  # Error but harmless (no args)
    "mv *",  # Move/rename files and directories
    "python --version",  # Check Python version
    "python -m *",  # Run Python module
    "python3 --version",  # Check Python 3 version
    "python3 -m *",  # Run Python 3 module
    "pip list",  # List installed Python packages
    "pip show *",  # Show details about Python packages
    "pip freeze",  # Output installed packages in requirements format
    "uv list",  # List installed Python packages (using uv)
    "uv pip list",  # List installed Python packages (using uv)
    "uv pip show *",  # Show details about Python packages (using uv)
    "uv pip freeze",  # Output installed packages (using uv)
    "cloc",  # Count lines of code (current dir)
    "cloc *",  # Count lines of code
    "git",  # Show git help (no args)
    "git *",  # Git version control commands
    "date",  # Display current date and time
    "cal",  # Display calendar
    "uptime",  # Show how long system has been running
    "whoami",  # Display current user ID
    "id",  # Display user and group IDs
    "uname",  # Print system information (no args)
    "uname *",  # Print system information
    "df",  # Report file system disk space usage (no args)
    "df *",  # Report file system disk space usage
    "du",  # Estimate file space usage (current dir)
    "du *",  # Estimate file space usage
    "wc",  # Wait for stdin (no args)
    "wc *",  # Print newline, word, and byte counts for files
    "less",  # Wait for stdin (no args)
    "less *",  # Pager for viewing files (interactive)
    "more",  # Wait for stdin (no args)
    "more *",  # Pager for viewing files (interactive)
    "diff",  # Error but harmless (no args)
    "diff *",  # Compare files line by line
    "comm",  # Error but harmless (no args)
    "comm *",  # Compare two sorted files line by line
    "sort",  # Wait for stdin (no args)
    "sort *",  # Sort lines of text files
    "uniq",  # Wait for stdin (no args)
    "uniq *",  # Report or omit repeated lines
    "ps",  # Report process status (no args)
    "ps *",  # Report process status
    "top",  # Display system processes (interactive)
    "env",  # Display environment variables
    "printenv",  # Print all environment variables (no args)
    "printenv *",  # Print environment variables
    "export -p",  # List exported environment variables
    "man",  # Error but harmless (no args)
    "man *",  # Display manual pages
    "info",  # Show info directory (no args)
    "info *",  # Display command information (GNU)
    "tldr",  # Show tldr pages index (no args)
    "tldr *",  # Simplified man pages
    "* --help",  # Common pattern for command help
    "stat",  # Error but harmless (no args)
    "stat *",  # Display file or file system status
    "which",  # Error but harmless (no args)
    "which *",  # Locate a command
    "whereis",  # Error but harmless (no args)
    "whereis *",  # Locate binary, source, and manual page for command
    "type",  # Error but harmless (no args)
    "type *",  # Describe how a command name would be interpreted
    "history",  # Display command history
    "clear",  # Clear the terminal screen
    "ping",  # Error but harmless (no args)
    "ping *",  # Check network connectivity to a host
    "ip",  # Show IP commands (no args)
    "ip *",  # Show / manipulate routing, network devices, interfaces (read-only use like 'ip addr')
    "ifconfig",  # Show network interfaces (no args)
    "ifconfig *",  # Configure network interfaces (often used read-only)
    "netstat",  # Print network connections (no args)
    "netstat *",  # Print network connections, routing tables, interface stats (read-only options often safe)
    "ss",  # Display socket statistics (no args)
    "ss *",  # Socket statistics (modern replacement for netstat, read-only options safe)
    "host",  # Error but harmless (no args)
    "host *",  # DNS lookup utility
    "dig",  # Show dig help (no args)
    "dig *",  # DNS lookup utility (more detailed)
    "nslookup",  # Interactive mode (no args)
    "nslookup *",  # DNS lookup utility (interactive/non-interactive)
    "tar -tvf *",  # List contents of a tar archive
    "zipinfo *",  # List detailed information about a ZIP archive
    "unzip -l *",  # List contents of a ZIP archive
    "gzip -l *",  # Display compression statistics for gzip files
    "gunzip -l *",  # Display compression statistics for gzip files (same as gzip -l)
    "zcat *",  # Display contents of gzipped files
    "bzcat *",  # Display contents of bzip2 compressed files
    "xzcat *",  # Display contents of xz compressed files
    "basename *",  # Strip directory and suffix from filenames
    "dirname *",  # Strip last component from file name
    "readlink *",  # Read value of a symbolic link
    "test *",  # Check file types and compare values (shell builtin)
    "[ * ]",  # Alternate syntax for 'test' (shell builtin)
    "alias",  # List defined aliases
    "jobs",  # List active jobs
    "file",  # Error but harmless (no args)
    "file *",  # Determine file type
    "rg *",
]

# Shell command execution timeout in seconds
SHELL_COMMAND_TIMEOUT = 60

# Approval statuses that indicate the operation should proceed
APPROVAL_STATUSES_OK = ["approved", "session_approved"]


# --- Rich CLI Theme Configuration ---
DEFAULT_SYNTAX_HIGHLIGHT_THEME = (
    "rrt"  # Default theme for syntax highlighting in Markdown code blocks
)


MODELS = (
    {
        "name": "gemini-2.5-pro",
        "model": "openrouter/google/gemini-2.5-pro-preview-06-05",
        "description": "Preview 06-05 (OPENROUTER)",
    },
    {
        "name": "gemini-2.5-flash",
        "model": "openrouter/google/gemini-2.5-flash-preview-05-20",
        "description": "Preview 05-20 (OPENROUTER)",
        "accepts": ("thinking"),
    },
)
