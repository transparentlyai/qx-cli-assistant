TITLE: Implementing Custom MarkItDown DocumentConverter (Python)
DESCRIPTION: Defines the structure for a custom DocumentConverter implementation in Python. This class is responsible for determining if it can process a given file stream (`accepts`) and performing the conversion to Markdown (`convert`). It handles binary input streams and returns a `DocumentConverterResult`.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_0

LANGUAGE: python
CODE:
```
from typing import BinaryIO, Any
from markitdown import MarkItDown, DocumentConverter, DocumentConverterResult, StreamInfo

class RtfConverter(DocumentConverter):

    def __init__(
        self, priority: float = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT
    ):
        super().__init__(priority=priority)

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
	
	# Implement logic to check if the file stream is an RTF file
	# ...
	raise NotImplementedError()


    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:

	# Implement logic to convert the file stream to Markdown
	# ...
	raise NotImplementedError()
```

----------------------------------------

TITLE: Defining MarkItDown Plugin Entry Point (Python)
DESCRIPTION: Defines the necessary global variable for the plugin interface version and the main `register_converters` function. MarkItDown calls this function during initialization to allow plugins to register their custom converter instances. It demonstrates how to instantiate and register an `RtfConverter` instance.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_1

LANGUAGE: python
CODE:
```
# The version of the plugin interface that this plugin uses. 
# The only supported version is 1 for now.
__plugin_interface_version__ = 1 

# The main entrypoint for the plugin. This is called each time MarkItDown instances are created.
def register_converters(markitdown: MarkItDown, **kwargs):
    """
    Called during construction of MarkItDown instances to register converters provided by plugins.
    """

    # Simply create and attach an RtfConverter instance
    markitdown.register_converter(RtfConverter())
```

----------------------------------------

TITLE: Converting File Using MarkItDown Plugins (Python)
DESCRIPTION: Shows how to enable plugin support programmatically when creating a MarkItDown instance in Python. By setting `enable_plugins=True`, the instance will load registered plugins via their entry points. It then demonstrates calling the `convert` method on a file path, which will utilize the enabled plugins if they accept the file type.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_6

LANGUAGE: python
CODE:
```
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True) 
result = md.convert("path-to-file.rtf")
print(result.text_content)
```

----------------------------------------

TITLE: Configuring Claude Desktop with markitdown-mcp Docker volume mount JSON
DESCRIPTION: This JSON configuration entry for Claude Desktop includes arguments for a Docker volume mount. Add this to 'claude_desktop_config.json' to allow the markitdown-mcp server running in Docker, when launched by Claude Desktop, to access local files via the specified mount.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_7

LANGUAGE: json
CODE:
```
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": [
  "run",
  "--rm",
  "-i",
  "-v",
  "/home/user/data:/workdir",
  "markitdown-mcp:latest"
      ]
    }
  }
}
```

----------------------------------------

TITLE: Converting File Using MarkItDown Plugins (Bash)
DESCRIPTION: Demonstrates how to use the MarkItDown command-line tool to convert a file while enabling installed plugins. The `--use-plugins` flag ensures that registered converters, such as the custom RTF converter, are considered. The command specifies the path to the file to be converted.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
markitdown --use-plugins path-to-file.rtf
```

----------------------------------------

TITLE: Listing Installed MarkItDown Plugins (Bash)
DESCRIPTION: Shows how to use the MarkItDown command-line interface to list all installed and recognized plugins. This command (`markitdown --list-plugins`) is a useful way to verify that the plugin was successfully installed and is available to MarkItDown. It displays the names of loaded plugins.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
markitdown --list-plugins
```

----------------------------------------

TITLE: Installing MarkItDown Plugin Locally (Bash)
DESCRIPTION: Provides the command to install the plugin package locally in editable mode using pip. This installation method is useful during development as changes to the source code are immediately reflected without needing to reinstall. It installs the package located in the current directory.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
pip install -e .
```

----------------------------------------

TITLE: Running markitdown-mcp Docker container with volume mount Bash
DESCRIPTION: This command runs the Docker container and mounts a local directory (e.g., '/home/user/data') to a path ('/workdir') inside the container. This allows the markitdown-mcp server running inside Docker to access local files via the mounted path.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
docker run -it --rm -v /home/user/data:/workdir markitdown-mcp:latest
```

----------------------------------------

TITLE: Converting File using MarkItDown API (Python)
DESCRIPTION: Shows how to use the MarkItDown class programmatically in Python to convert a file (e.g., XLSX). Instantiates the class, calls the `convert` method, and prints the extracted text content. Requires the package to be installed and imported.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown/README.md#_snippet_3

LANGUAGE: python
CODE:
```
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("test.xlsx")
print(result.text_content)
```

----------------------------------------

TITLE: Configuring Claude Desktop with markitdown-mcp Docker JSON
DESCRIPTION: Add this JSON entry to the 'mcpServers' section of your Claude Desktop configuration file ('claude_desktop_config.json'). This configures Claude Desktop to launch the markitdown-mcp server inside a Docker container using the standard arguments.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_6

LANGUAGE: json
CODE:
```
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "markitdown-mcp:latest"
      ]
    }
  }
}
```

----------------------------------------

TITLE: Converting File using MarkItDown Python API with LLM for Image Description
DESCRIPTION: Shows how to integrate an LLM client (like OpenAI) with the `MarkItDown` Python class to provide descriptions for images found within documents during conversion.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_10

LANGUAGE: python
CODE:
```
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("example.jpg")
print(result.text_content)
```

----------------------------------------

TITLE: Configuring MarkItDown Plugin Entry Point (TOML)
DESCRIPTION: Configures the project's entry points in the `pyproject.toml` file. This setup allows MarkItDown to discover the plugin package and load its `register_converters` function. The key identifies the plugin, and the value is the Python package path.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-sample-plugin/README.md#_snippet_2

LANGUAGE: toml
CODE:
```
[project.entry-points."markitdown.plugin"]
sample_plugin = "markitdown_sample_plugin"
```

----------------------------------------

TITLE: Printing String in Python
DESCRIPTION: This snippet prints the literal string "markitdown" to the standard output using Python's built-in print function. It serves as a basic test or demonstration. No external dependencies are required. Input: None. Output: The string "markitdown" followed by a newline.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown/tests/test_files/test_notebook.ipynb#_snippet_0

LANGUAGE: python
CODE:
```
print("markitdown")
```

----------------------------------------

TITLE: Launching mcpinspector tool Bash
DESCRIPTION: Execute this command using npx (Node Package Execute), which requires Node.js and npm/yarn/pnpm. This launches the mcpinspector tool, a web-based utility for debugging Model Context Protocol servers.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_8

LANGUAGE: bash
CODE:
```
npx @modelcontextprotocol/inspector
```

----------------------------------------

TITLE: Specifying markitdown-mcp command for mcpinspector STDIO Bash
DESCRIPTION: When using the mcpinspector tool to debug an STDIO server, this command string is provided as the 'command' input field within the mcpinspector interface to specify the server executable it should run and connect to.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_9

LANGUAGE: bash
CODE:
```
markitdown-mcp
```

----------------------------------------

TITLE: Printing Integer with Comment in Python
DESCRIPTION: This snippet demonstrates printing an integer value in Python following a line comment. It shows basic code structure and output. No external dependencies are required. Input: None. Output: The integer `42` followed by a newline.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown/tests/test_files/test_notebook.ipynb#_snippet_1

LANGUAGE: python
CODE:
```
# comment in code
print(42)
```

----------------------------------------

TITLE: Running markitdown-mcp SSE server Bash
DESCRIPTION: This command starts the markitdown-mcp server using the Server-Sent Events (SSE) transport. It binds the server to the specified host (127.0.0.1) and port (3001) for network access via SSE.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
markitdown-mcp --sse --host 127.0.0.1 --port 3001
```

----------------------------------------

TITLE: Installing MarkItDown from Source using Git and Pip
DESCRIPTION: This snippet demonstrates how to clone the MarkItDown repository from GitHub and install the package in editable mode along with all optional dependencies using pip.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
git clone git@github.com:microsoft/markitdown.git
cd markitdown
pip install -e 'packages/markitdown[all]'
```

----------------------------------------

TITLE: Basic File Conversion using MarkItDown Python API
DESCRIPTION: Demonstrates the fundamental usage of the `MarkItDown` class in Python to convert a file and access the resulting text content. It shows how to instantiate the class and call the `convert` method.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_8

LANGUAGE: python
CODE:
```
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
result = md.convert("test.xlsx")
print(result.text_content)
```

----------------------------------------

TITLE: Installing Specific Optional Dependencies via Pip
DESCRIPTION: Explains how to install only selected optional dependencies (e.g., for PDF, DOCX, PPTX support) instead of all using bracket notation with pip.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
pip install 'markitdown[pdf, docx, pptx]'
```

----------------------------------------

TITLE: Running markitdown-mcp Docker container Bash
DESCRIPTION: Use this command to run the markitdown-mcp Docker image interactively. The '--rm' flag ensures the container is automatically removed upon exit, and '-i' keeps stdin open.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
docker run -it --rm markitdown-mcp:latest
```

----------------------------------------

TITLE: Running markitdown-mcp STDIO server Bash
DESCRIPTION: Execute this command in your terminal to start the markitdown-mcp server using the default STDIO transport mechanism. The server will listen for MCP commands on standard input and output results on standard output.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
markitdown-mcp
```

----------------------------------------

TITLE: Converting File using MarkItDown CLI (Bash)
DESCRIPTION: Demonstrates converting a specified file (e.g., PDF) to Markdown using the `markitdown` command-line utility. The output is redirected to a Markdown file. Requires the package to be installed and in the system's PATH.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
markitdown path-to-file.pdf > document.md
```

----------------------------------------

TITLE: Converting File using MarkItDown Python API with Azure Document Intelligence
DESCRIPTION: Illustrates how to configure the `MarkItDown` Python class to use Azure Document Intelligence for conversion by providing the `docintel_endpoint` during initialization.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_9

LANGUAGE: python
CODE:
```
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

----------------------------------------

TITLE: Building markitdown-mcp Docker image Bash
DESCRIPTION: Run this command in the directory containing the Dockerfile to build a Docker image for markitdown-mcp. The image is tagged locally as 'markitdown-mcp:latest' and can then be run as a container.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
docker build -t markitdown-mcp:latest .
```

----------------------------------------

TITLE: Installing markitdown-mcp Python package Bash
DESCRIPTION: Use this command to install the markitdown-mcp package and its dependencies from the Python Package Index (PyPI) using pip. This command requires Python and pip to be installed on your system.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install markitdown-mcp
```

----------------------------------------

TITLE: Installing MarkItDown from Source (Bash)
DESCRIPTION: Clones the MarkItDown repository from GitHub and installs the package in editable mode (-e) including all optional dependencies. Requires Git and pip.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
git clone git@github.com:microsoft/markitdown.git
cd markitdown
pip install -e packages/markitdown[all]
```

----------------------------------------

TITLE: Using Azure Document Intelligence via MarkItDown CLI
DESCRIPTION: Details the command-line arguments (`-d`, `-e`) required to utilize the Azure Document Intelligence service for file conversion, specifying the endpoint.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_7

LANGUAGE: bash
CODE:
```
markitdown path-to-file.pdf -o document.md -d -e "<document_intelligence_endpoint>"
```

----------------------------------------

TITLE: Converting File via CLI Redirecting Output
DESCRIPTION: Shows basic command-line usage to convert a file (e.g., PDF) to Markdown and redirect the standard output to a specified file.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
markitdown path-to-file.pdf > document.md
```

----------------------------------------

TITLE: Installing MarkItDown from PyPI (Bash)
DESCRIPTION: Installs the MarkItDown package and all optional dependencies from the Python Package Index (PyPI) using pip. Requires pip to be installed.
SOURCE: https://github.com/microsoft/markitdown/blob/main/packages/markitdown/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install markitdown[all]
```

----------------------------------------

TITLE: Enabling Plugins via MarkItDown CLI
DESCRIPTION: Shows how to enable installed 3rd-party plugins when performing a file conversion using the command-line interface.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_6

LANGUAGE: bash
CODE:
```
markitdown --use-plugins path-to-file.pdf
```

----------------------------------------

TITLE: Running MarkItDown in Docker Container
DESCRIPTION: Demonstrates how to run the MarkItDown Docker container, piping a local file's content as input and redirecting the output.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_12

LANGUAGE: sh
CODE:
```
docker run --rm -i markitdown:latest < ~/your-file.pdf > output.md
```

----------------------------------------

TITLE: Listing Installed MarkItDown Plugins via CLI
DESCRIPTION: Provides the command-line instruction to list all 3rd-party plugins that are currently installed for MarkItDown.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
markitdown --list-plugins
```

----------------------------------------

TITLE: Running Pre-commit Checks
DESCRIPTION: Command to run pre-commit hooks across all files, ensuring code quality and consistency before submitting a pull request.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_17

LANGUAGE: sh
CODE:
```
pre-commit run --all-files
```

----------------------------------------

TITLE: Converting File via CLI Specifying Output File
DESCRIPTION: Demonstrates using the `-o` flag in the command line to specify the output Markdown file directly.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
markitdown path-to-file.pdf -o document.md
```

----------------------------------------

TITLE: Entering Hatch Shell Environment
DESCRIPTION: Command to enter the shell environment managed by hatch, which is typically configured for running project tasks like tests.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_15

LANGUAGE: sh
CODE:
```
hatch shell
```

----------------------------------------

TITLE: Installing Hatch for Testing
DESCRIPTION: Instructs how to install the `hatch` build and test tool using pip.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_14

LANGUAGE: sh
CODE:
```
pip install hatch  # Other ways of installing hatch: https://hatch.pypa.io/dev/install/
```

----------------------------------------

TITLE: Running Tests using Hatch
DESCRIPTION: Provides the command to execute the project's tests using the hatch tool, either within a hatch shell or a suitable environment.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_16

LANGUAGE: sh
CODE:
```
hatch test
```

----------------------------------------

TITLE: Converting File via CLI Piping Input
DESCRIPTION: Illustrates converting a file by piping its content to the MarkItDown command-line tool.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
cat path-to-file.pdf | markitdown
```

----------------------------------------

TITLE: Building MarkItDown Docker Image
DESCRIPTION: Provides the command to build a Docker image for MarkItDown from the project's Dockerfile.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_11

LANGUAGE: sh
CODE:
```
docker build -t markitdown:latest .
```

----------------------------------------

TITLE: Navigating to MarkItDown Package Directory
DESCRIPTION: A simple shell command to change the current directory to the MarkItDown package within the repository.
SOURCE: https://github.com/microsoft/markitdown/blob/main/README.md#_snippet_13

LANGUAGE: sh
CODE:
```
cd packages/markitdown
```
