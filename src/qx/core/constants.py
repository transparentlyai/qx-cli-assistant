# qx/core/constants.py

# Default model name if not specified by the user
DEFAULT_MODEL = "gemini-1.5-flash-001" # Example, adjust as needed

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
]

# Default prohibited commands for the execute_shell tool
# Uses fnmatch patterns
DEFAULT_PROHIBITED_COMMANDS = [
    "sudo*",
    "su",
    "rm -rf /",
    "mkfs*",
    "fdisk*",
    "dd*",
    "shutdown*",
    "reboot*",
    "halt*",
    "poweroff*",
    "passwd*",
    "useradd*",
    "userdel*",
    "groupadd*",
    "groupdel*",
    "chown -R * /", # Overly broad chown
    "chmod -R * /", # Overly broad chmod
    "iptables*",
    "ufw*",
    "firewall-cmd*",
    # Network commands that should use the 'fetch' tool or are risky
    "curl*",
    "wget*",
    "ping*",
    "ssh*",
    "scp*",
    "ftp*",
    "telnet*",
    "nc*",
    "netcat*",
    # Process management that could be disruptive
    "killall*",
    "pkill*",
    # Specific dangerous constructs
    ":(){:|:&};:", # Fork bomb
    "* > /dev/sda*", # Direct disk write
    "mv / /dev/null", # Moving critical directories
    "mv * /dev/null", # Moving all files in cwd to /dev/null
    # Git commands that could alter remote state without explicit multi-step approval
    # "git push*", # Consider if this should be allowed with approval or a dedicated tool
    # "git fetch*", # Generally safe, but could be noisy
    # "git pull*", # Can have merge conflicts, might be better handled
]

# Shell command execution timeout in seconds
SHELL_COMMAND_TIMEOUT = 60

# --- Default LLM Provider Settings (Example values, primarily for reference) ---
# These are not directly used by QX core logic if PydanticAI handles defaults,
# but can be useful for documentation or future direct API integrations.

# OpenAI
DEFAULT_OPENAI_MODEL = "gpt-4-turbo"
DEFAULT_OPENAI_TEMPERATURE = 0.7
DEFAULT_OPENAI_MAX_TOKENS = 2048
DEFAULT_OPENAI_TOKENS_PER_MIN = 40000  # Example TPM for some models

# Anthropic
DEFAULT_ANTHROPIC_MODEL = "claude-3-opus-20240229"
DEFAULT_ANTHROPIC_TEMPERATURE = 0.7
DEFAULT_ANTHROPIC_MAX_TOKENS = 4096
DEFAULT_ANTHROPIC_TOKENS_PER_MIN = 25000 # Example TPM

# Google Vertex AI
DEFAULT_VERTEXAI_MODEL = "gemini-1.5-pro-001" # Or "gemini-1.0-pro"
DEFAULT_VERTEXAI_LOCATION = "us-central1" # Example location
DEFAULT_VERTEXAI_TEMPERATURE = 0.7
DEFAULT_VERTEXAI_MAX_TOKENS = 8192
DEFAULT_VERTEXAI_TOKENS_PER_MIN = 60000 # Example TPM

# Groq
DEFAULT_GROQ_MODEL = "llama3-70b-8192"
DEFAULT_GROQ_TEMPERATURE = 0.7
DEFAULT_GROQ_MAX_TOKENS = 8192
DEFAULT_GROQ_TOKENS_PER_MIN = 300000 # Example TPM (Groq is fast)


# --- Rich CLI Themes ---
# These themes can be used with Rich Console for consistent styling.
# Add more themes or customize existing ones as needed.
CLI_THEMES = {
    "dark": {
        "default": "bright_white on default",
        "info": "bright_cyan on default",
        "warning": "bright_yellow on default",
        "error": "bold bright_red on default",
        "success": "bright_green on default",
        "debug": "dim white on default",
        "prompt": "bold bright_blue on default",
        "user_input": "white on default",
        "title": "bold bright_magenta on default",
        "path": "bright_blue underline on default",
        "code": "bright_yellow on default",
        "highlight": "black on bright_yellow",
        "table.header": "bold bright_white on blue",
        "table.cell": "bright_white on default", # General cell style
        "table.row.odd": "bright_white on grey19",
        "table.row.even": "bright_white on grey23",
        "table.border": "bright_blue",
        "log.time": "dim cyan on default",
        "log.path": "dim blue on default",
        "log.level.debug": "dim white on default",
        "log.level.info": "bright_cyan on default",
        "log.level.warning": "bright_yellow on default",
        "log.level.error": "bold bright_red on default",
        "log.level.critical": "bold white on red",
        "progress.bar": "bright_green",
        "progress.text": "bright_white on default", # For text within progress context
        "progress.description": "bright_white on default",
        "progress.percentage": "bright_magenta on default",
        "progress.remaining": "dim bright_cyan on default",
        "repr.str": "bright_green on default",
        "repr.number": "bright_cyan on default",
        "repr.bool_true": "bold bright_green on default",
        "repr.bool_false": "bold bright_red on default",
        "repr.none": "dim bright_magenta on default",
        "repr.url": "underline bright_blue on default",
        "repr.tag_name": "dim bright_white on default",
        "repr.tag_value": "bright_cyan on default",
        "rule.line": "dim white",
        "rule.text": "bright_white on default",
        "markdown.h1": "bold bright_magenta underline on default",
        "markdown.h2": "bold bright_magenta on default",
        "markdown.h3": "bold bright_blue on default",
        "markdown.paragraph": "bright_white on default",
        "markdown.block_quote": "italic bright_cyan on grey23",
        "markdown.list": "bright_white on default",
        "markdown.code": "bright_yellow on grey23",
        "markdown.code_block": "bright_yellow on grey19",
        "markdown.link": "underline bright_blue on default",
        "markdown.link_url": "dim bright_blue on default",
        "markdown.strong": "bold bright_white on default",
        "markdown.emphasis": "italic bright_white on default",
        "markdown.hr": "dim white",
    },
    "light": {
        "default": "black on default",
        "info": "blue on default",
        "warning": "orange3 on default",
        "error": "bold red on default",
        "success": "green on default",
        "debug": "dim black on default",
        "prompt": "bold dark_blue on default",
        "user_input": "black on default",
        "title": "bold magenta on default",
        "path": "dark_blue underline on default",
        "code": "purple4 on default",
        "highlight": "white on dark_slate_gray2",
        "table.header": "bold black on bright_cyan",
        "table.cell": "black on default", # General cell style
        "table.row.odd": "black on grey93",
        "table.row.even": "black on grey89",
        "table.border": "blue",
        "log.time": "dim blue_violet on default",
        "log.path": "dim dark_blue on default",
        "log.level.debug": "dim black on default",
        "log.level.info": "blue on default",
        "log.level.warning": "orange3 on default",
        "log.level.error": "bold red on default",
        "log.level.critical": "bold white on red",
        "progress.bar": "green",
        "progress.text": "black on default", # For text within progress context
        "progress.description": "black on default",
        "progress.percentage": "magenta on default",
        "progress.remaining": "dim blue_violet on default",
        "repr.str": "green4 on default",
        "repr.number": "cyan on default",
        "repr.bool_true": "bold green on default",
        "repr.bool_false": "bold red on default",
        "repr.none": "dim magenta on default",
        "repr.url": "underline blue on default",
        "repr.tag_name": "dim black on default",
        "repr.tag_value": "blue on default",
        "rule.line": "dim black",
        "rule.text": "black on default",
        "markdown.h1": "bold magenta underline on default",
        "markdown.h2": "bold magenta on default",
        "markdown.h3": "bold blue on default",
        "markdown.paragraph": "black on default",
        "markdown.block_quote": "italic blue on grey93",
        "markdown.list": "black on default",
        "markdown.code": "purple4 on grey93",
        "markdown.code_block": "purple4 on grey89",
        "markdown.link": "underline blue on default",
        "markdown.link_url": "dim blue on default",
        "markdown.strong": "bold black on default",
        "markdown.emphasis": "italic black on default",
        "markdown.hr": "dim black",
    }
}