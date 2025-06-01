# Prject QX Directives

- project shhould be modulear and extensible. no module should be more than 1000 lines of code. if a module is more than 650 lines of code, break it down into smaller modules.
- QX is a coding cli agent built by Transparently.AI
- prioritize using packages over writing custom code 
- read documentation .Q/documentation for latest libraries and packages documentation
- use uv for package management. Only uv, not pip or conda or poetry.
- the environment is already inititalized with the latest version of uv. only add packages with uv add
- if you need to create temporary scirpts, files, ad other artifacts,use the tmp directory - remember to remove them after the task is done.
- Do not use relative imports 

