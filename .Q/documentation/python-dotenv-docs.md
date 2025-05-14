TITLE: Installing python-dotenv Python
DESCRIPTION: Provides the standard command-line instruction to install the python-dotenv library using pip, the Python package installer.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_0

LANGUAGE: shell
CODE:
```
pip install python-dotenv
```

----------------------------------------

TITLE: Installing python-dotenv
DESCRIPTION: This command installs the core python-dotenv library using pip. It is the standard way to add the library as a dependency to your Python project.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_0

LANGUAGE: shell
CODE:
```
pip install python-dotenv
```

----------------------------------------

TITLE: Loading .env Variables into Environment (Python)
DESCRIPTION: Demonstrates how to use `load_dotenv()` to load variables from a .env file into the application's environment (os.environ). This is the primary method for making .env variables available to code that expects environment configuration.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_1

LANGUAGE: python
CODE:
```
from dotenv import load_dotenv

load_dotenv()  # take environment variables

# Code of your application, which uses environment variables (e.g. from `os.environ` or
# `os.getenv`) as if they came from the actual environment.
```

----------------------------------------

TITLE: Loading .env with load_dotenv Python
DESCRIPTION: Demonstrates the basic usage of `load_dotenv()` to load variables from a default `.env` file into the script's environment, making them available via `os.environ` or `os.getenv`.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_1

LANGUAGE: python
CODE:
```
from dotenv import load_dotenv

load_dotenv()  # take environment variables

# Code of your application, which uses environment variables (e.g. from `os.environ` or
# `os.getenv`) as if they came from the actual environment.
```

----------------------------------------

TITLE: Loading .env Variables into Dictionary (Python)
DESCRIPTION: Shows how to use the `dotenv_values()` function to parse a .env file and return its contents as a dictionary without modifying the actual environment variables. This is useful for reading configuration without global side effects.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_3

LANGUAGE: python
CODE:
```
from dotenv import dotenv_values

config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}
```

----------------------------------------

TITLE: Loading .env as Dictionary Python
DESCRIPTION: Shows how to use `dotenv_values()` to read the contents of a `.env` file into a Python dictionary, providing access to the configuration without modifying the process environment.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_3

LANGUAGE: python
CODE:
```
from dotenv import dotenv_values

config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}
```

----------------------------------------

TITLE: Defining Variables in .env Bash
DESCRIPTION: Illustrates the basic syntax for defining key-value pairs in a `.env` file, including comments and POSIX-style variable expansion using `${VAR}` syntax.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_2

LANGUAGE: bash
CODE:
```
# Development settings
DOMAIN=example.org
ADMIN_EMAIL=admin@${DOMAIN}
ROOT_URL=${DOMAIN}/app
```

----------------------------------------

TITLE: Example .env File with Variable Expansion (Bash/env)
DESCRIPTION: An example .env file content illustrating basic key-value assignment, comments, and variable expansion using the ${VAR_NAME} syntax. Values are parsed and can reference other variables defined earlier in the file or in the environment.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
# Development settings
DOMAIN=example.org
ADMIN_EMAIL=admin@${DOMAIN}
ROOT_URL=${DOMAIN}/app
```

----------------------------------------

TITLE: Loading dotenv Extension in IPython
DESCRIPTION: This IPython magic command loads the python-dotenv extension, making the %dotenv magic available for interactive sessions. This is the first step to using dotenv within IPython.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_6

LANGUAGE: python
CODE:
```
%load_ext dotenv
```

----------------------------------------

TITLE: Loading .env in IPython Shell
DESCRIPTION: Explains how to use the `dotenv` IPython extension and `%dotenv` magic command to load environment variables from a .env file directly within an IPython session.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_6

LANGUAGE: shell
CODE:
```
%load_ext dotenv
%dotenv
```

LANGUAGE: shell
CODE:
```
%dotenv relative/or/absolute/path/to/.env
```

----------------------------------------

TITLE: Installing python-dotenv CLI
DESCRIPTION: Installs the python-dotenv library along with the command-line interface extras. This is required to use the `dotenv` command in your terminal.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_9

LANGUAGE: shell
CODE:
```
pip install "python-dotenv[cli]"
```

----------------------------------------

TITLE: Using dotenv Command-line Interface Shell
DESCRIPTION: Showcases common usage of the `dotenv` CLI commands to set, list, and execute other programs with variables loaded from the .env file.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_7

LANGUAGE: shell
CODE:
```
$ pip install "python-dotenv[cli]"
$ dotenv set USER foo
$ dotenv set EMAIL foo@example.org
$ dotenv list
USER=foo
EMAIL=foo@example.org
$ dotenv list --format=json
{
  "USER": "foo",
  "EMAIL": "foo@example.org"
}
$ dotenv run -- python foo.py
```

----------------------------------------

TITLE: Running Command with dotenv CLI (Shell)
DESCRIPTION: The `dotenv run -- <command>` structure loads variables from the .env file into the environment specifically for the duration of the specified command, providing a scoped way to run applications with .env config.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_14

LANGUAGE: shell
CODE:
```
dotenv run -- python foo.py
```

----------------------------------------

TITLE: Merging .env Configs and Environment Python
DESCRIPTION: Provides an example of advanced configuration management by merging variables loaded from multiple .env files and overriding them with existing process environment variables using dictionary unpacking.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_4

LANGUAGE: python
CODE:
```
import os
from dotenv import dotenv_values

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    **os.environ,  # override loaded values with environment variables
}
```

----------------------------------------

TITLE: Merging .env and Environment Variables (Python)
DESCRIPTION: Illustrates an advanced configuration pattern where variables from multiple .env files are combined and then potentially overridden by existing environment variables, creating a single configuration dictionary.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_4

LANGUAGE: python
CODE:
```
import os
from dotenv import dotenv_values

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    **os.environ  # override loaded values with environment variables
}
```

----------------------------------------

TITLE: Listing Variables via dotenv CLI (Shell)
DESCRIPTION: The `dotenv list` command displays the variables found in the .env file, formatted as key=value pairs. This is useful for inspecting the file's content.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_12

LANGUAGE: shell
CODE:
```
dotenv list
```

----------------------------------------

TITLE: Setting Variable via dotenv CLI (Shell)
DESCRIPTION: Uses the `dotenv set` command to add or update a key-value pair in the .env file. This provides a convenient way to manage .env file content from the command line.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_10

LANGUAGE: shell
CODE:
```
dotenv set USER foo
```

----------------------------------------

TITLE: Setting Another Variable via dotenv CLI (Shell)
DESCRIPTION: Another example demonstrating the `dotenv set` command to add or update a different variable, illustrating how multiple variables can be managed.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_11

LANGUAGE: shell
CODE:
```
dotenv set EMAIL foo@example.org
```

----------------------------------------

TITLE: Listing Variables as JSON via dotenv CLI (Shell)
DESCRIPTION: Uses the `--format=json` option with `dotenv list` to output the variables from the .env file in JSON format. This is useful for scripting and integration.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_13

LANGUAGE: shell
CODE:
```
dotenv list --format=json
```

----------------------------------------

TITLE: Loading .env from Stream Python
DESCRIPTION: Demonstrates how to load configuration from a file-like object or stream (like StringIO) using the `stream` argument of `load_dotenv`, useful for sources other than the filesystem.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_5

LANGUAGE: python
CODE:
```
from io import StringIO

from dotenv import load_dotenv

config = StringIO("USER=foo\nEMAIL=foo@example.org")
load_dotenv(stream=config)
```

----------------------------------------

TITLE: Loading .env from a Stream (Python)
DESCRIPTION: Demonstrates using `load_dotenv()` with the `stream` argument to read configuration directly from a Python stream object (like `StringIO`) instead of a file path, enabling loading from non-filesystem sources.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_5

LANGUAGE: python
CODE:
```
from io import StringIO

from dotenv import load_dotenv

config = StringIO("USER=foo\nEMAIL=foo@example.org")
load_dotenv(stream=config)
```

----------------------------------------

TITLE: Loading Default .env in IPython
DESCRIPTION: After loading the extension, this IPython magic command searches for and loads the .env file using `find_dotenv()`, setting variables in the current IPython session's environment.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_7

LANGUAGE: python
CODE:
```
%dotenv
```

----------------------------------------

TITLE: Loading Specific .env in IPython
DESCRIPTION: Allows specifying a relative or absolute path to a .env file to load in IPython, overriding the default search behavior. Optional flags can modify loading behavior.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_8

LANGUAGE: python
CODE:
```
%dotenv relative/or/absolute/path/to/.env
```

----------------------------------------

TITLE: Running Tests with Tox - Shell
DESCRIPTION: This snippet shows a single shell command to execute the project's test suite using the tox automation tool. Tox handles setting up virtual environments and running tests across different configurations as defined in the project's tox.ini file. Requires tox to be installed globally or accessible in the environment.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/contributing.md#_snippet_1

LANGUAGE: shell
CODE:
```
$ tox
```

----------------------------------------

TITLE: Executing Tests with Tox Shell
DESCRIPTION: Uses the tox automation tool to run tests in multiple configured environments, typically simulating different Python versions or dependency sets. This provides a more robust testing approach compared to running tests in a single environment.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/CONTRIBUTING.md#_snippet_1

LANGUAGE: Shell
CODE:
```
$ tox
```

----------------------------------------

TITLE: Executing Tests Python Project Shell
DESCRIPTION: Installs core development and test dependencies from requirements.txt, installs the current project package in editable mode, runs the flake8 linter for code style checks, and executes the test suite using pytest. This is the standard manual workflow for running tests.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/CONTRIBUTING.md#_snippet_0

LANGUAGE: Shell
CODE:
```
$ pip install -r requirements.txt
$ pip install -e .
$ flake8
$ pytest
```

----------------------------------------

TITLE: Running Tests with Pip/Pytest - Shell
DESCRIPTION: This snippet provides a sequence of shell commands to install development dependencies from `requirements.txt`, install the project in editable mode, run the flake8 linter, and execute the pytest test suite. It covers the standard test execution flow using these tools.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/contributing.md#_snippet_0

LANGUAGE: shell
CODE:
```
$ pip install -r requirements.txt
$ pip install -e .
$ flake8
$ pytest
```

----------------------------------------

TITLE: Building/Serving Documentation Locally with MkDocs - Shell
DESCRIPTION: These shell commands guide the user through installing the documentation-specific dependencies from `requirements-docs.txt`, installing the project in editable mode, and then starting the mkdocs development server. This allows contributors to preview documentation changes locally before submitting them.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/contributing.md#_snippet_2

LANGUAGE: shell
CODE:
```
$ pip install -r requirements-docs.txt
$ pip install -e .
$ mkdocs serve
```

----------------------------------------

TITLE: Building Documentation MkDocs Shell
DESCRIPTION: Installs dependencies required specifically for building documentation from requirements-docs.txt, installs the project locally in editable mode, and serves the documentation site using MkDocs. This allows contributors to preview documentation changes locally via a web browser.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/CONTRIBUTING.md#_snippet_2

LANGUAGE: Shell
CODE:
```
$ pip install -r requirements-docs.txt
$ pip install -e .
$ mkdocs serve
```

----------------------------------------

TITLE: Multiline .env Value (Actual Newlines)
DESCRIPTION: Example in a .env file showing how a value enclosed in double quotes can span multiple lines directly. The actual newline characters are preserved as part of the value.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_15

LANGUAGE: bash
CODE:
```
FOO="first line
second line"
```

----------------------------------------

TITLE: Defining Multiline Values in .env Bash
DESCRIPTION: Illustrates how to define variable values that span multiple lines within a `.env` file using double quotes.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_8

LANGUAGE: bash
CODE:
```
FOO="first line
second line"
```

----------------------------------------

TITLE: Multiline .env Value (Explicit Newline)
DESCRIPTION: Example in a .env file showing how a value enclosed in double quotes can include the explicit `\n` escape sequence to represent a newline within a single line string.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_16

LANGUAGE: bash
CODE:
```
FOO="first line\nsecond line"
```

----------------------------------------

TITLE: .env Variable Without Value
DESCRIPTION: An example in a .env file showing a variable name listed without an equals sign or value. `dotenv_values` will associate this variable with `None`, while `load_dotenv` will ignore it.
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/README.md#_snippet_17

LANGUAGE: bash
CODE:
```
FOO
```

----------------------------------------

TITLE: Defining Variable Without Value in .env Bash
DESCRIPTION: Shows the syntax in a `.env` file for declaring a variable name without assigning any value, explaining its interpretation by `dotenv_values` (as `None`) versus `load_dotenv` (ignored).
SOURCE: https://github.com/theskumar/python-dotenv/blob/main/docs/index.md#_snippet_9

LANGUAGE: bash
CODE:
```
FOO
```
