# QX Directives System

Directives are reusable prompts that can be invoked using the `@` syntax to quickly inject common instructions or context into your conversations with QX.

## Overview

The directives system allows you to:
- Create reusable prompt templates as markdown files
- Quickly inject common instructions into your prompts
- Maintain consistency across similar tasks
- Share prompts across projects or with teams
- Override built-in directives with project-specific versions

## How Directives Work

When you type `@directivename` in your prompt, QX automatically replaces it with the full content of the corresponding markdown file. This happens before your message is sent to the AI, allowing you to quickly inject complex instructions without typing them repeatedly.

## Using Directives

To use a directive, simply type `@` followed by the directive name in your message:

```
Help me review this code @review
```

Multiple directives can be used in a single message:

```
@plan help me break down this feature, then @review check my approach
```

The directive content is expanded inline, so the AI sees your full message with all directive content included.

## Directive Discovery

QX discovers directives from two locations:

1. **Built-in Directives**: Located in `src/qx/directives/`
   - Ships with QX installation
   - Provides standard functionality
   
2. **Project Directives**: Located in `.Q/directives/` in your project root
   - User-defined, project-specific directives
   - Version controlled with your project
   - Override built-in directives if they have the same name

## Creating Custom Directives

To create a custom directive:

1. Create a `.md` file in your project's `.Q/directives/` directory
2. Name the file using lowercase letters and underscores (e.g., `code_analyzer.md`)
3. Write your prompt content in the file

Example `.Q/directives/security_check.md`:
```markdown
Perform a security audit focusing on:
- Input validation and sanitization
- Authentication and authorization checks
- Sensitive data exposure
- Common vulnerability patterns (OWASP Top 10)
- Dependency vulnerabilities

Provide specific recommendations with severity levels.
```

## Built-in Directives

QX comes with five built-in directives:

### @worklog
Maintains a detailed work log for tracking progress, decisions, and next steps. Helps track project evolution, document decision rationale, and maintain continuity across sessions.

### @review
Acts as a thorough code reviewer focusing on:
- Security vulnerabilities
- Performance issues
- Code quality and maintainability
- Best practices adherence
- Test coverage suggestions

### @plan
Helps break down complex features into manageable implementation steps. Creates structured plans with task dependencies, effort estimates, and clear success criteria.

### @commit
Assists with creating well-formatted git commit messages following conventional commit standards. Analyzes staged changes and suggests appropriate commit messages.

### @lint
Provides code linting and style guidance specific to the programming language and project conventions. Focuses on code consistency and readability.

## Autocomplete Support

The QX prompt provides intelligent autocomplete for directives:
- Type `@` and press Tab to see all available directives
- The autocomplete shows the directive name and first line as a description
- Works for both built-in and project-specific directives
- Updates dynamically as you add new directives

## Best Practices

1. **Keep directives focused**: Each directive should have a single, clear purpose
2. **Use descriptive names**: Choose names that clearly indicate what the directive does
3. **Include context**: Provide enough context in the directive for effective use
4. **Version control**: Include project directives in your version control system
5. **Document complex directives**: Add comments or examples for team members

## Examples

### Development Workflow
```
@worklog Starting work on authentication feature
@plan Help me design the auth system architecture
```

### Code Review Process
```
I've implemented the user login endpoint @review
```

### Security Analysis
```
@review Focus on security implications of this database query function
```

### Git Workflow
```
@commit I've staged my changes for the new feature
```

### Code Quality
```
@lint Check this Python class for style issues
```

## Advanced Usage

### Chaining Directives
Combine multiple directives for comprehensive assistance:
```
@plan break this down, then @review check each component
```

### Project-Specific Overrides
Override built-in directives by creating a file with the same name in `.Q/directives/`:
```
.Q/directives/review.md  # This overrides the built-in @review directive
```

### Directive Naming
- Use lowercase letters and underscores only
- The filename (without .md) becomes the directive name
- Examples: `code_analyzer.md` → `@code_analyzer`, `security_check.md` → `@security_check`

### Team Collaboration
Share directives across your team by committing them to your project repository:
```bash
git add .Q/directives/
git commit -m "Add team coding standards directive"
```

## Technical Details

### Directive Manager
The directive system is managed by the `DirectiveManager` class (`src/qx/core/directive_manager.py`):
- Singleton pattern ensures consistent directive discovery
- Lazy loading for performance
- Caches directives after first discovery
- Handles both built-in and project directories

### Integration Points
- **CLI Integration**: `src/qx/cli/qprompt.py` handles `@directive` expansion
- **Autocomplete**: `src/qx/cli/completer.py` provides tab completion
- **Pattern Matching**: Uses regex `@(\w+)` to find directives in user input

## Troubleshooting

- **Directive not found**: 
  - Check the file exists in `.Q/directives/` or built-in location
  - Ensure file uses `.md` extension
  - Verify filename uses only lowercase and underscores
  
- **Autocomplete not working**: 
  - Type `@` followed by Tab
  - Check that `.Q/directives/` directory exists if using project directives
  
- **Wrong directive loaded**: 
  - Project directives override built-in ones
  - Check for naming conflicts in `.Q/directives/`
  
- **Directive content not expanding**:
  - Ensure you're using the exact directive name (case-sensitive)
  - Check for typos in the `@directivename` syntax

## Future Enhancements

Planned features for the directives system:
- Parameterized directives with placeholders
- Conditional directive content
- Directive composition and inheritance
- Global user directives in `~/.config/qx/directives/`