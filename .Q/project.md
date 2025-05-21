# Prject QX Directives

- this project is a re-write of the q project found at ~/projects/q - use the original q project as a reference
- project shhould be modulear and extensible. no module should be more than 1000 lines of code. if a module is more than 650 lines of code, break it down into smaller modules.
- QX is a coding cli agent built by Transparently.AI
- QX is writen in python using the PydaticAI framework as it core
- prioritize using packages over writing custom code 
- read documentation .Q/documentation for latest libraries and packages documentation
- when you are not sure about something, ask 
- always consult the .Q/technical-specs.md 
- keep the documentation up to date 
- keep the code simple. avoid unnecessary complexity. use libraries and packages when possible. avoid deeply nested code.
- use version control (git) for all code.
- use uv for package management. Only uv , not pip or conda or poetry.
- the environment is already inititalized with the latest version of uv. only add packages with uv add
- use the existing pyproject.toml file for package management.
- if you need to create temporary scirpts, files, ad other artifacts,use the tmp directory.
- do not use relative imports 

