# Stage changes and create a comprehensive git commit

## Commit Workflow & Best Practices

Follow these steps to create a well-structured git commit:

### 1. Analyze Changes
First, examine all changes to understand what has been modified:
- Run `git status` to see all modified and untracked files
- Run `git diff` to review unstaged changes
- Run `git diff --staged` to review already staged changes
- Identify the purpose and scope of the changes

### 2. Group Related Changes
- Stage files that belong together using `git add`
- If changes span multiple features or fixes, consider splitting into separate commits
- Each commit should represent one logical change

### 3. Write a Comprehensive Commit Message

#### Message Format
Follow the Conventional Commits specification:

**Structure:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**IMPORTANT:** Do NOT use backticks in the actual commit message. The above is just for formatting clarity.

#### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, semicolons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvements
- **test**: Adding or modifying tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

#### Commit Message Guidelines
1. **Subject line** (first line):
   - Use imperative mood ("Add feature" not "Added feature")
   - Capitalize the first letter
   - No period at the end
   - Keep under 50 characters
   - Be specific and descriptive

2. **Body** (optional, after blank line):
   - Explain WHAT changed and WHY, not HOW
   - Wrap at 72 characters
   - Use bullet points for multiple items
   - Reference issue numbers if applicable

3. **Footer** (optional):
   - Breaking changes: Start with "BREAKING CHANGE:"
   - Issue references: "Fixes #123" or "Closes #456"
   - Co-authors: "Co-authored-by: Name <email>"

### 4. Examples of Good Commit Messages

**Simple commit:**
```
feat: Add user authentication via OAuth2
```

**Commit with body:**
```
fix: Prevent race condition in payment processing

The payment service was vulnerable to double-charging when users
clicked submit multiple times. This adds a mutex lock around the
payment processing logic and includes a unique transaction ID check.

Fixes #789
```

**Breaking change:**
```
feat!: Update API response format for user endpoints

BREAKING CHANGE: API responses now use camelCase instead of snake_case.
All client applications need to update their response parsing logic.

The change improves consistency with JavaScript conventions and
reduces the need for case conversion in frontend applications.
```

### 5. Stage and Commit
After crafting your message:
1. Stage all relevant files: `git add <files>` or `git add -A` for all changes
2. Create the commit with your message
3. Verify the commit with `git log -1 --stat`

### 6. Quality Checklist
Before finalizing the commit, ensure:
- [ ] Changes are related and belong in a single commit
- [ ] Commit message clearly explains the change
- [ ] No debugging code or console.log statements included
- [ ] Tests pass (if applicable)
- [ ] Code follows project style guidelines
- [ ] Sensitive information (API keys, passwords) is not included

### 7. Common Pitfalls to Avoid
- Don't commit commented-out code
- Avoid generic messages like "fix bug" or "update code"
- Don't mix formatting changes with functional changes
- Never use backticks in commit messages
- Avoid commits that are too large - aim for atomic commits

Remember: A good commit history tells the story of your project's evolution and helps future developers (including yourself) understand why changes were made.