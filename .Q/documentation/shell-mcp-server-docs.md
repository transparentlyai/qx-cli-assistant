TITLE: Successful Command Response Format JSON
DESCRIPTION: This JSON snippet shows the format for a successful command execution response. It includes standard output (`stdout`), standard error (`stderr`), the exit status code (`status`), and the execution time.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_13

LANGUAGE: json
CODE:
```
{
    "stdout": "command output",
    "stderr": "",
    "status": 0,
    "execution_time": 0.123
}
```

----------------------------------------

TITLE: Basic Command Execution Request Format JSON
DESCRIPTION: This JSON snippet shows the basic structure for a command execution request. The `command` field is a string array containing the command and its arguments.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_9

LANGUAGE: json
CODE:
```
{
    "command": ["ls", "-l", "/tmp"]
}
```

----------------------------------------

TITLE: Error Command Response Format JSON
DESCRIPTION: This JSON snippet shows the format for an unsuccessful command execution response. It includes an `error` message describing the failure (e.g., command not allowed), the exit status, and often duplicated error information in `stderr`.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_14

LANGUAGE: json
CODE:
```
{
    "error": "Command not allowed: rm",
    "status": 1,
    "stdout": "",
    "stderr": "Command not allowed: rm",
    "execution_time": 0
}
```

----------------------------------------

TITLE: Configuring MCP Shell Server for Published Version JSON
DESCRIPTION: This JSON snippet shows how to configure the mcp-shell-server within the Claude desktop client's configuration file for a published version. It specifies the command to run (`uvx mcp-shell-server`) and sets the `ALLOW_COMMANDS` environment variable.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_1

LANGUAGE: json
CODE:
```
{
  "mcpServers": {
    "shell": {
      "command": "uvx",
      "args": [
        "mcp-shell-server"
      ],
      "env": {
        "ALLOW_COMMANDS": "ls,cat,pwd,grep,wc,touch,find"
      }
    },
  }
}
```

----------------------------------------

TITLE: Opening Claude Client Config File Shell
DESCRIPTION: This command opens the Claude desktop application's configuration file in a code editor. This file is used to define and configure MCP servers like the mcp-shell-server for use within the client.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_0

LANGUAGE: shell
CODE:
```
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

----------------------------------------

TITLE: Installing MCP Shell Server via pip Bash
DESCRIPTION: This command installs the mcp-shell-server package from the Python Package Index (PyPI) using pip. This is the standard way to install the server for local use.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
pip install mcp-shell-server
```

----------------------------------------

TITLE: Showing ALLOW_COMMANDS Environment Variable Format Bash
DESCRIPTION: This snippet shows the basic format for setting the `ALLOW_COMMANDS` environment variable, listing whitelisted commands separated by commas.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_6

LANGUAGE: bash
CODE:
```
ALLOW_COMMANDS="ls,cat,echo"
```

----------------------------------------

TITLE: Starting MCP Shell Server with ALLOW_COMMANDS Bash
DESCRIPTION: This command starts the mcp-shell-server using the `uvx` executable, which ensures the necessary environment is active. It sets the `ALLOW_COMMANDS` environment variable to whitelist specific commands.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
ALLOW_COMMANDS="ls,cat,echo" uvx mcp-shell-server
```

----------------------------------------

TITLE: Starting MCP Shell Server with ALLOWED_COMMANDS Alias Bash
DESCRIPTION: This command demonstrates starting the mcp-shell-server using the alias `ALLOWED_COMMANDS` for the environment variable, which serves the same purpose as `ALLOW_COMMANDS`.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
ALLOWED_COMMANDS="ls,cat,echo" uvx mcp-shell-server
```

----------------------------------------

TITLE: Command Execution Request with Directory and Timeout JSON
DESCRIPTION: This JSON snippet shows how to specify both a working directory and a timeout for a command execution request. The `directory` field sets the path where the command will be executed.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_12

LANGUAGE: json
CODE:
```
{
    "command": ["grep", "-r", "pattern"],
    "directory": "/path/to/search",
    "timeout": 60
}
```

----------------------------------------

TITLE: Command Execution Request with Stdin JSON
DESCRIPTION: This JSON snippet shows how to include standard input in a command execution request. The `stdin` field contains the string data to be piped to the command.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_10

LANGUAGE: json
CODE:
```
{
    "command": ["cat"],
    "stdin": "Hello, World!"
}
```

----------------------------------------

TITLE: Command Execution Request with Timeout JSON
DESCRIPTION: This JSON snippet demonstrates setting a timeout for a command execution request. The `timeout` field specifies the maximum execution time in seconds.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_11

LANGUAGE: json
CODE:
```
{
    "command": ["long-running-process"],
    "timeout": 30
}
```

----------------------------------------

TITLE: Running Tests with pytest Bash
DESCRIPTION: This command executes the test suite for the mcp-shell-server using the pytest framework. Running tests is essential during development to ensure code changes do not introduce regressions.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_17

LANGUAGE: bash
CODE:
```
pytest
```

----------------------------------------

TITLE: Installing Development Dependencies Bash
DESCRIPTION: This command installs the mcp-shell-server package in editable mode (`-e`) along with its test dependencies (`.[test]`). This is necessary for running tests and developing the server.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_16

LANGUAGE: bash
CODE:
```
pip install -e ".[test]"
```

----------------------------------------

TITLE: Cloning Repository for Development Bash
DESCRIPTION: This command sequence clones the mcp-shell-server GitHub repository and changes the current directory into the cloned repository. This is the first step in setting up a local development environment.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_15

LANGUAGE: bash
CODE:
```
git clone https://github.com/yourusername/mcp-shell-server.git
cd mcp-shell-server
```

----------------------------------------

TITLE: Configuring MCP Shell Server for Local Version JSON
DESCRIPTION: This JSON snippet demonstrates the configuration for a locally installed version of mcp-shell-server within the Claude client config. It uses `uv run` to execute the server from the current directory and sets the `ALLOW_COMMANDS` environment variable.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_2

LANGUAGE: json
CODE:
```
{
  "mcpServers": {
    "shell": {
      "command": "uv",
      "args": [
        "--directory",
        ".",
        "run",
        "mcp-shell-server"
      ],
      "env": {
        "ALLOW_COMMANDS": "ls,cat,pwd,grep,wc,touch,find"
      }
    },
  }
}
```

----------------------------------------

TITLE: Showing ALLOWED_COMMANDS Format with Spaces Bash
DESCRIPTION: This snippet illustrates that the `ALLOWED_COMMANDS` environment variable (or its alias) can handle spaces around the commas separating whitelisted commands.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_7

LANGUAGE: bash
CODE:
```
ALLOWED_COMMANDS="ls ,echo, cat"
```

----------------------------------------

TITLE: Showing ALLOW_COMMANDS Format with Multiple Spaces Bash
DESCRIPTION: This snippet confirms that the `ALLOW_COMMANDS` environment variable can handle multiple spaces around the commas separating whitelisted commands.
SOURCE: https://github.com/tumf/mcp-shell-server/blob/main/README.md#_snippet_8

LANGUAGE: bash
CODE:
```
ALLOW_COMMANDS="ls,  cat  , echo"
```
