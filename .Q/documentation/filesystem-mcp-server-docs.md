TITLE: Running Filesystem MCP Server (Bash)
DESCRIPTION: Commands to start the built server executable using node directly or via the npm start script from the project root.
SOURCE: https://github.com/cyanheads/filesystem-mcp-server/blob/main/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
node dist/index.js
# Or if you are in the project root:
# npm start
```

----------------------------------------

TITLE: Configuring Filesystem MCP Server in MCP Client (JSON)
DESCRIPTION: A conceptual JSON configuration example showing how to add the filesystem-mcp-server to an MCP client's settings, including specifying the command, arguments, and environment variables like FS_BASE_DIRECTORY and LOG_LEVEL.
SOURCE: https://github.com/cyanheads/filesystem-mcp-server/blob/main/README.md#_snippet_4

LANGUAGE: json
CODE:
```
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": ["/path/to/filesystem-mcp-server/dist/index.js"],
      "env": {
        "FS_BASE_DIRECTORY": "/path/to/base/directory",
        "LOG_LEVEL": "debug"
      },
      "disabled": false,
      "autoApprove": []
    }
    // ... other servers
  }
}
```

----------------------------------------

TITLE: Installing Filesystem MCP Server Dependencies (Bash)
DESCRIPTION: Command to install the necessary project dependencies listed in the package.json file using npm.
SOURCE: https://github.com/cyanheads/filesystem-mcp-server/blob/main/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
npm install
```

----------------------------------------

TITLE: Cloning Filesystem MCP Server Repository (Bash)
DESCRIPTION: Instructions to clone the filesystem-mcp-server repository from GitHub and navigate into the project directory using the command line.
SOURCE: https://github.com/cyanheads/filesystem-mcp-server/blob/main/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
git clone https://github.com/cyanheads/filesystem-mcp-server.git
cd filesystem-mcp-server
```

----------------------------------------

TITLE: Building Filesystem MCP Server (Bash)
DESCRIPTION: Command to build the TypeScript project, compiling source code into JavaScript and preparing the executable file in the dist/ directory.
SOURCE: https://github.com/cyanheads/filesystem-mcp-server/blob/main/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
npm run build
```

----------------------------------------

TITLE: Running Project Structure Tree Command (Shell)
DESCRIPTION: Executes the `npm run tree` script defined in `package.json` to display a live, detailed view of the project's directory structure in the console.
SOURCE: https://github.com/cyanheads/filesystem-mcp-server/blob/main/README.md#_snippet_5

LANGUAGE: Shell
CODE:
```
npm run tree
```
