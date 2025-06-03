# Prject QX Directives

- project shhould be modulear and extensible. no module should be more than 1000 lines of code. if a module is more than 650 lines of code, break it down into smaller modules.
- prioritize using packages over writing custom code 
- read documentation .Q/documentation for latest libraries and packages documentation
- use uv for package management e.g. `uv add <package-name>`, `uv remove <package-name>`, `uv tree`, etc.
- the environment is already inititalized with the latest version of uv. only add packages with uv add
- if you need to create temporary scirpts, files, and other artifacts, use the ./tmp directory - remember to remove them after the task is done.
- Do not use relative imports 

# for python code
Limit the scope to the file you are working and apply the following directives in the order they are listed:
    1. Compile code using `python -m py_compile <file.py>`
    2. Run mypy for type checking e.g. `mypy <file.py>`
    2. Use ruff for linting and formatting e.g. `ruff check <file.py>` and `ruff format <file.py>`
