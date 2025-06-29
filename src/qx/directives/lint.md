# Type check, lint, and format code

## Analysis & Tool Discovery

### 1. First, identify the project's primary language(s)
Examine the codebase to determine what languages are being used:
- Check file extensions in the current directory and subdirectories
- Look for configuration files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.)
- Identify the dominant language(s) that need linting

### 2. Discover available tools
Check what tools are already installed or configured in the project:

#### For Python projects:
- **Type checking**: Look for `pyright`, `mypy`, `pyre`, or `pytype`
  - Check for config files: `pyrightconfig.json`, `mypy.ini`, `.mypy.ini`, `setup.cfg` with [mypy] section
- **Linting**: Look for `ruff`, `flake8`, `pylint`, `bandit` (security)
  - Check for config files: `ruff.toml`, `.ruff.toml`, `.flake8`, `.pylintrc`
- **Formatting**: Look for `ruff format`, `black`, `yapf`, `autopep8`, `isort` (imports)
  - Check for config files: `pyproject.toml`, `.black`, `.yapfrc`
- **All-in-one**: `ruff` (preferred if available - does linting and formatting)

#### For JavaScript/TypeScript projects:
- **Type checking**: `tsc` (TypeScript compiler)
  - Check for: `tsconfig.json`
- **Linting**: `eslint`, `tslint` (deprecated), `biome`
  - Check for: `.eslintrc.*`, `eslint.config.js`
- **Formatting**: `prettier`, `eslint --fix`, `biome format`
  - Check for: `.prettierrc.*`, `prettier.config.js`

#### For Rust projects:
- **Type checking**: `cargo check`
- **Linting**: `cargo clippy`
- **Formatting**: `cargo fmt`
- Check for: `Cargo.toml`, `rustfmt.toml`, `.rustfmt.toml`

#### For Go projects:
- **Type checking**: `go build` (built-in)
- **Linting**: `golangci-lint`, `go vet`
- **Formatting**: `gofmt`, `goimports`
- Check for: `go.mod`, `.golangci.yml`

#### For Java projects:
- **Type checking**: `javac` (built-in)
- **Linting**: `checkstyle`, `spotbugs`, `pmd`
- **Formatting**: `google-java-format`, `spotless`
- Check for: `pom.xml`, `build.gradle`, `checkstyle.xml`

#### For C/C++ projects:
- **Type checking**: Compiler warnings (`gcc -Wall`, `clang -Wall`)
- **Linting**: `clang-tidy`, `cppcheck`, `cpplint`
- **Formatting**: `clang-format`
- Check for: `.clang-format`, `.clang-tidy`

### 3. Execution Strategy

#### Step 1: Check for existing scripts
First, check if the project has pre-configured scripts:
- `package.json`: Look for scripts like `lint`, `format`, `type-check`, `check`
- `Makefile`: Look for targets like `lint`, `format`, `check`
- `pyproject.toml`: Check for tool configurations or scripts
- `tox.ini`, `nox.py`: Python testing/linting automation

#### Step 2: Run tools in order
1. **Type checking first** - Catches the most serious issues
2. **Linting second** - Finds code quality issues
3. **Formatting last** - Auto-fixes style issues

#### Step 3: Use project's preferred tools
- If config files exist, use those tools even if others are available
- Respect existing tool configurations (don't override settings)
- If multiple tools are configured, run all of them

### 4. Command Examples by Language

After discovering available tools, run them appropriately:

**Python:**
```bash
# Type checking
mypy .                    # or
pyright                   # or
python -m pypy_check

# Linting
ruff check .              # or
flake8                    # or
pylint **/*.py

# Formatting
ruff format .             # or
black .                   # or
yapf -r -i .
```

**JavaScript/TypeScript:**
```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint              # or
npx eslint .              # or
npx biome check .

# Formatting  
npm run format            # or
npx prettier --write .    # or
npx eslint . --fix
```

**Rust:**
```bash
cargo check
cargo clippy -- -D warnings
cargo fmt
```

**Go:**
```bash
go build ./...
golangci-lint run
gofmt -w .
```

### 5. Handling Missing Tools

If no tools are found:
1. Check if the project has a `requirements-dev.txt`, `package.json` devDependencies, or similar
2. Suggest installing appropriate tools for the detected language
3. Provide basic fallback commands (like compiler warnings)

### 6. Error Handling

- If a tool fails, continue with the next one
- Collect all errors and warnings
- Present a summary at the end
- Distinguish between errors (must fix) and warnings (should fix)

### 7. CI/CD Integration Check

Look for CI configuration files to understand the project's standards:
- `.github/workflows/*.yml` - GitHub Actions
- `.gitlab-ci.yml` - GitLab CI
- `.travis.yml` - Travis CI
- `azure-pipelines.yml` - Azure DevOps
- `.circleci/config.yml` - CircleCI

These often define the exact commands the project uses for linting.

Remember: The goal is to use the project's existing setup and standards, not impose new ones.