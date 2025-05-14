# Prject QX Directives

- QX is a coding cli agent built by Transparently.AI
- QX is writen in python using the PydaticAI framework as it core
- prioritize using packages over writing custom code 
- read documentation .Q/documentation for latest libraries and packages documentation
- when you are not sure about something, ask 
- always consult the .Q/technical-specs.md 
- keep a detail log of activities and sprints in .Q/projectlog.md - keep enough context to ensure a new session can pick up where you left off.
- keep the documentation up to date 
- keep the code simple. avoid unnecessary complexity. use libraries and packages when possible. avoid deeply nested code.
- use version control (git) for all code.
- use uv for package management. Only uv , not pip or conda or poetry.
- the environment is already inititalized with the latest version of uv. only add packages with uv add
- use the existing pyproject.toml file for package management.
- at the start of every session read the .Q/projectlog.md file for the latest updates and context.
- if you need to create temporary scirpts, files, ad other artifacts,use the tmp directory.
