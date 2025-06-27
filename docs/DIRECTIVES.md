# QX Directives System

Directives are reusable prompts that can be invoked using the `@` syntax to quickly inject common instructions or context into your conversations with QX.

## Overview

The directives system allows you to:
- Create reusable prompt templates
- Quickly access common instructions
- Maintain consistency across similar tasks
- Share prompts across projects or with teams

## Using Directives

To use a directive, simply type `@` followed by the directive name in your message:

```
Help me review this code @reviewer
```

Multiple directives can be used in a single message:

```
@planner help me break down this feature, then @reviewer check my approach
```

## Directive Discovery

QX discovers directives from two locations:

1. **Built-in Directives**: Located in `src/qx/directives/`
2. **Project Directives**: Located in `.Q/directives/` in your project root

Project directives take precedence over built-in directives with the same name.

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

QX comes with several built-in directives:

### @worklogger
Maintains a detailed work log for tracking progress, decisions, and next steps. Optimized for LLM context management.

### @reviewer
Acts as a thorough code reviewer focusing on security, performance, code quality, and best practices.

### @planner
Helps break down complex tasks into manageable steps with dependencies, milestones, and effort estimates.

## Autocomplete Support

The QX prompt supports autocomplete for directives. Type `@` and press Tab to see available directives with descriptions.

## Best Practices

1. **Keep directives focused**: Each directive should have a single, clear purpose
2. **Use descriptive names**: Choose names that clearly indicate what the directive does
3. **Include context**: Provide enough context in the directive for effective use
4. **Version control**: Include project directives in your version control system
5. **Document complex directives**: Add comments or examples for team members

## Examples

### Development Workflow
```
@worklogger Starting work on authentication feature
@planner Help me design the auth system architecture
```

### Code Review Process
```
I've implemented the user login endpoint @reviewer
```

### Security Analysis
```
@reviewer Focus on security implications of this database query function
```

## Advanced Usage

### Chaining Directives
Combine multiple directives for comprehensive assistance:
```
@planner break this down, then @reviewer check each component
```

### Project-Specific Overrides
Override built-in directives by creating a file with the same name in `.Q/directives/`:
```
.Q/directives/reviewer.md  # This overrides the built-in @reviewer
```

### Team Collaboration
Share directives across your team by committing them to your project repository:
```bash
git add .Q/directives/
git commit -m "Add team coding standards directive"
```

## Troubleshooting

- **Directive not found**: Check the file exists and uses `.md` extension
- **Autocomplete not working**: Ensure the directive manager has discovered your files
- **Wrong directive loaded**: Check for naming conflicts between project and built-in directives

## Future Enhancements

Planned features for the directives system:
- Parameterized directives with placeholders
- Conditional directive content
- Directive composition and inheritance
- Global user directives in `~/.config/qx/directives/`