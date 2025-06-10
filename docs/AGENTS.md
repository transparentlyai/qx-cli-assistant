# QX Agent Management Guide

QX features a powerful modular agent system that allows you to create, manage, and switch between different AI assistants, each with their own specialized roles, tools, and behaviors.

## Quick Start

### Autocomplete Support

QX provides intelligent autocomplete for all agent commands. Simply start typing and press Tab:

- `/ag` + Tab → `/agents`
- `/agents ` + Tab → shows `list`, `switch`, `info`, `reload`
- `/agents switch ` + Tab → shows all available agents with descriptions
- `/agents switch c` + Tab → completes to `code_reviewer`

### Viewing Available Agents

To see all available agents:
```
/agents list
```

### Switching Between Agents

#### Runtime Agent Switching
You can now switch agents during an active QX session:

```
/agents switch <agent_name>
```

This will:
- Load the new agent configuration
- Create a new LLM agent instance with the agent's model and settings
- Replace the active agent immediately
- The new agent will respond to your next query

Example:
```
/agents switch code_reviewer
```

#### Pre-loading Agents (Alternative Method)
You can also start QX with a specific agent pre-loaded using the `QX_DEFAULT_AGENT` environment variable:

```bash
# Set the default agent before starting QX
export QX_DEFAULT_AGENT=code_reviewer
qx

# Or set it for a single session
QX_DEFAULT_AGENT=code_reviewer qx

# Examples with different agents
QX_DEFAULT_AGENT=documentation_writer qx "help me write docs for this project"
QX_DEFAULT_AGENT=devops_automation qx "review my docker setup"
QX_DEFAULT_AGENT=data_processor qx "analyze this CSV file"

# You can also set it in your shell profile for permanent use
echo 'export QX_DEFAULT_AGENT=code_reviewer' >> ~/.bashrc
```


### Current Agent Info

To see which agent is currently active:
```
/agents info
```

### Reloading Agents

To reload an agent's configuration from disk:
```
/agents reload [agent_name]
```

If no agent name is provided, the current agent will be reloaded.

### Refreshing Agent Discovery

To refresh agent discovery and find new project agents:
```
/agents refresh
```

This is useful when:
- You've added new `.agent.yaml` files to `.Q/agents/`
- You've switched to a different project directory
- You want to pick up newly created agents without restarting QX

## Understanding Agents

### What are Agents?

Agents in QX are specialized AI assistants defined by YAML configuration files. Each agent has:

- **Role**: What the agent specializes in (e.g., code review, documentation writing)
- **Instructions**: Detailed guidelines for how the agent should behave
- **Tools**: Which tools the agent has access to
- **Model Configuration**: LLM model settings and parameters
- **Execution Mode**: How the agent operates (interactive, autonomous, or hybrid)

### Default Agent

QX comes with a default agent called `qx` located at `/src/qx/agents/qx.agent.yaml`. This is a general-purpose software engineering agent that starts automatically when you run QX.

### Built-in Specialized Agents

QX includes several pre-configured specialized agents:

1. **code_reviewer** - Security-focused code analysis and review
2. **devops_automation** - Infrastructure automation and deployment
3. **documentation_writer** - Technical writing and documentation
4. **data_processor** - Data analysis and processing tasks

## Agent Discovery

QX discovers agents from multiple locations in order of priority:

1. **Local agents**: `./src/qx/agents/` (highest priority - for QX development)
2. **Project agents**: `./.Q/agents/` (project-specific agents)
3. **User agents**: `~/.config/qx/agents/` (user-wide agents)
4. **System agents**: `/etc/qx/agents/` (lowest priority - system-wide agents)

Agents in higher-priority locations override those with the same name in lower-priority locations.

### Project-Specific Agents

Project agents in `./.Q/agents/` are automatically discovered when you run QX from any directory within your project. This allows you to:

- **Create project-specific agents** tailored to your current codebase
- **Share agents with your team** by committing them to version control
- **Override system agents** with project-specific versions
- **Maintain different agent configurations** for different projects

#### Quick Project Agent Setup

```bash
# Create the project agents directory
mkdir -p .Q/agents

# Create a project-specific agent
cat > .Q/agents/project_helper.agent.yaml << 'EOF'
name: "Project Helper"
enabled: true
description: "Specialist for this specific project"
role: You are a specialist for this specific project.
instructions: |
  Help with tasks specific to this codebase.
  You understand the project structure and conventions.
tools: [read_file_tool, write_file_tool, execute_shell_tool]
model:
  name: openrouter/anthropic/claude-3.5-sonnet
EOF

# Refresh agent discovery and switch to your new agent
/agents refresh
/agents switch project_helper
```

## Creating Custom Agents

### Minimal Agent (Quick Start)

The simplest agent requires these mandatory fields:

```yaml
# minimal_agent.agent.yaml
name: "My Helper"
enabled: true
description: "A helpful assistant for general tasks"
role: You are a helpful assistant.
instructions: Answer questions and help users with their tasks.
```

**That's it!** The system applies sensible defaults for everything else.

### Practical Minimal Agent (Recommended)

For most use cases, include tools and model settings:

```yaml
# my_agent.agent.yaml
name: "Domain Specialist"
enabled: true
description: "Specialized assistant for [your domain]"
role: You are a specialized assistant for [your domain].

instructions: |
  Help users with [specific tasks].
  Be helpful and accurate.

tools: [
  read_file_tool,
  write_file_tool,
  execute_shell_tool
]

model:
  name: openrouter/google/gemini-2.5-pro-preview-06-05
```

### Quick Examples

**Code Helper:**
```yaml
# code_helper.agent.yaml
name: "Code Helper"
enabled: true
description: "Coding assistant for development tasks"
role: You are a coding assistant.
instructions: Help write and debug code.
tools: [read_file_tool, write_file_tool, execute_shell_tool]
```

**Documentation Bot:**
```yaml
# docs_bot.agent.yaml
name: "Documentation Bot"
enabled: true
description: "Documentation writer and maintainer"
role: You are a documentation writer.
instructions: Create clear, helpful documentation.
tools: [read_file_tool, write_file_tool, web_fetch_tool]
```

**Data Analyst:**
```yaml
# analyst.agent.yaml
name: "Data Analyst"
enabled: true
description: "Data analysis and insights specialist"
role: You are a data analyst.
instructions: Analyze data and provide insights.
tools: [read_file_tool, web_fetch_tool]
```

### File Requirements

- **Filename**: Must end with `.agent.yaml`
- **Location**: Place in any discovery directory:
  - `./src/qx/agents/` (local project)
  - `~/.config/qx/agents/` (user-wide)
  - `/etc/qx/agents/` (system-wide)
- **Agent Name**: Derived from filename (`my_helper.agent.yaml` → `my_helper`)

### Mandatory Fields

Every agent configuration must include these required fields:

- **name**: Display name for the agent (string)
- **enabled**: Whether the agent is available for use (boolean)
- **description**: Brief description of the agent's purpose (string)
- **role**: The agent's persona and expertise (string)
- **instructions**: Detailed operational guidelines (string)

### Agent Types

Agents can be categorized by type to control their visibility:

- **type: "user"** (default): Regular agents shown to users in CLI/UI
- **type: "system"**: Backend agents for internal tasks, hidden from user interfaces

```yaml
# User-facing agent (default)
name: "My Assistant"
enabled: true
description: "General purpose assistant"
type: "user"  # Optional, defaults to "user"
role: You are a helpful assistant.
instructions: Help users with their tasks.

# System agent for internal use
name: "Context Compressor"
enabled: true
description: "System agent for compressing context"
type: "system"  # Hidden from user interfaces
role: You compress and summarize information.
instructions: Efficiently compress text while preserving key information.
```

System agents are useful for:
- Context compression and summarization
- Background processing tasks
- Internal system operations
- Data transformation pipelines

The backend can use filtering methods to discover only user agents or system agents as needed.

### Testing Your Agent

```bash
# List all agents (including your new one)
/agents list

# Switch to your new agent
/agents switch my_agent

# Test the agent
who are you?
```

### Default Values Applied

When using minimal configuration, these defaults are automatically applied. **All defaults can be overridden using QX_ environment variables:**

```yaml
# Automatic defaults for minimal agents (configurable via environment variables)
name: "qx_agent"                           # QX_AGENT_NAME
version: "1.0.0"                           # QX_AGENT_VERSION  
description: "QX Agent"                    # QX_AGENT_DESCRIPTION
tools: []                                  # QX_AGENT_TOOLS (comma-separated)
model:
  name: "openrouter/anthropic/claude-3.5-sonnet"  # QX_MODEL_NAME
  parameters:
    temperature: 0.73                      # QX_AGENT_TEMPERATURE
    max_tokens: 4096                       # QX_AGENT_MAX_TOKENS
    top_p: 1.0                            # QX_AGENT_TOP_P
    frequency_penalty: 0.0                # QX_AGENT_FREQUENCY_PENALTY
    presence_penalty: 0.0                 # QX_AGENT_PRESENCE_PENALTY
    reasoning_budget: "medium"            # QX_AGENT_REASONING_BUDGET
execution:
  mode: interactive                       # QX_AGENT_EXECUTION_MODE
  max_execution_time: 300                # QX_AGENT_MAX_EXECUTION_TIME
  max_iterations: 10                     # QX_AGENT_MAX_ITERATIONS
  constraints:
    max_file_size: "10MB"                # QX_AGENT_MAX_FILE_SIZE
    allowed_paths: ["./"]                # QX_AGENT_ALLOWED_PATHS
    forbidden_paths: ["/etc","/sys","/proc"]  # QX_AGENT_FORBIDDEN_PATHS
    max_tool_calls_per_turn: 10          # QX_AGENT_MAX_TOOL_CALLS
```

### Environment Variable Configuration

You can customize agent defaults system-wide using environment variables in your `qx.conf` file:

```bash
# Agent behavior defaults
QX_AGENT_TEMPERATURE=0.3              # More conservative for code review
QX_AGENT_MAX_TOKENS=8192              # Longer responses
QX_AGENT_EXECUTION_MODE=autonomous     # Default to autonomous mode
QX_AGENT_TOOLS=read_file_tool,write_file_tool  # Default tool set

# Security defaults
QX_AGENT_ALLOWED_PATHS=./src,./docs   # Restrict file access
QX_AGENT_MAX_FILE_SIZE=1MB            # Smaller file size limit
QX_AGENT_APPROVAL_REQUIRED_TOOLS=execute_shell_tool  # Require approval
```

### Complete Agent Structure (Advanced)

For full control over agent behavior:

```yaml
# advanced_agent.agent.yaml
name: "Advanced Specialist"
enabled: true
description: "Specialized assistant for [your specific domain]"
type: "user"  # Optional, defaults to "user"

role: |
  You are a specialized assistant for [your specific domain].
  [Describe the agent's personality and expertise]

instructions: |
  ## Your Mission
  [Describe what the agent should accomplish]
  
  ## Core Capabilities
  - [List key capabilities]
  - [Each capability on its own line]
  
  ## Guidelines
  - [Specific rules and guidelines]
  - [How the agent should behave]

tools: [
  read_file_tool,
  write_file_tool,
  execute_shell_tool,
  web_fetch_tool,
  current_time_tool,
  todo_manager_tool
]

model:
  name: openrouter/google/gemini-2.5-pro-preview-06-05
  parameters:
    temperature: 0.7
    max_tokens: 8192
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0

execution:
  mode: interactive
  timeout: 300
  max_iterations: 10
```

### Advanced Configuration

For more advanced agent configurations, see the built-in agents as examples. You can configure:

- **Context Templates**: Dynamic content injection using variables
- **Lifecycle Hooks**: Actions to perform when agent starts/stops
- **Autonomous Mode**: For background task processing
- **Console Settings**: Custom output formatting and identification

### Template Variables

You can use template variables in your agent configuration that get replaced at runtime:

```yaml
context: |
  **User Context:**
  {user_context}
  
  **Project Context:**
  {project_context}
  
  **Current Directory:**
  {project_files}
```

## Execution Modes

### Interactive Mode (Default)

The agent responds to your inputs in real-time conversation:

```yaml
execution:
  mode: interactive
```

### Autonomous Mode

The agent runs independently in the background, processing tasks from a queue:

```yaml
execution:
  mode: autonomous
  autonomous_config:
    max_concurrent_tasks: 3
    poll_interval: 5.0
    heartbeat_interval: 30.0
    auto_restart: true
```

### Hybrid Mode

The agent can switch between interactive and autonomous operation:

```yaml
execution:
  mode: hybrid
```

## Best Practices

### Agent Naming

- Use descriptive names that indicate the agent's purpose
- Use lowercase with underscores (e.g., `code_reviewer`, `data_analyst`)
- Avoid generic names like `assistant` or `helper`

### Role Definition

- Be specific about the agent's expertise and domain
- Include personality traits that enhance the user experience
- Define the agent's scope and limitations

### Instructions

- Provide clear, actionable guidelines
- Include examples of good behavior when helpful
- Specify any domain-specific rules or constraints

### Tool Selection

- Only include tools the agent actually needs
- Consider security implications of tool access
- Test tool combinations to ensure compatibility

## Agent-to-Agent Communication

### How Agents Call Other Agents

Agents can interact with each other through several mechanisms:

#### 1. Agent Switching (Interactive)
```yaml
# An agent can switch to another agent for specialized tasks
tools: [agent_manager_tool]
```

The agent can then use:
- `switch_agent_tool(agent_name="code_reviewer")` - Switch to specialist
- `list_agents_tool()` - See available agents
- `get_current_agent_tool()` - Check current agent status

#### 2. Autonomous Agent Spawning (Background Tasks)
```python
# Start another agent as a background task
await agent_manager.start_autonomous_agent(
    agent_name="code_reviewer",
    context={
        "task": "Review authentication.py for security issues",
        "project_context": "Flask web application"
    }
)
```

#### 3. Agent Consultation (Load Agent Info)
```python
# Load another agent's configuration for consultation
agent_info = await agent_manager.load_agent("devops_automation")
# Use the specialist's knowledge without switching
```

### Practical Examples

**QX Agent Delegating to Specialist:**
```
User: "Please review my code for security issues"
QX: "I'll switch to our Code Review Specialist for this security-focused task."
*Calls switch_agent_tool(agent_name="code_reviewer")*
```

**Multi-Agent Workflow:**
```python
# Start multiple specialists for complex tasks
await start_autonomous_agent("code_reviewer", context={"task": "Security audit"})
await start_autonomous_agent("documentation_writer", context={"task": "Update docs"})
# Coordinate results from both specialists
```

**Agent Collaboration Chain:**
```
Code Reviewer: "Found deployment security issues. Consulting DevOps specialist..."
*Loads devops_automation agent configuration*
*Provides infrastructure-focused recommendations*
```

### Available Tools for Agent Communication

Include these tools in your agent configuration to enable inter-agent communication:

```yaml
tools: [
  # Core agent management
  agent_manager_tool,
  
  # File operations for sharing context
  read_file_tool,
  write_file_tool,
  
  # For background tasks
  todo_manager_tool
]
```

### Simple In-Code Agent Execution

The minimal code to start an agent with a task:

```python
from qx.core.agent_manager import get_agent_manager

# One-liner agent task execution
await get_agent_manager().start_autonomous_agent(
    "code_reviewer", 
    context={"task": "Review my authentication code"}
)
```

## Troubleshooting

### Agent Not Found

If an agent isn't found when switching:

1. Check the agent file exists in one of the discovery directories
2. Verify the YAML syntax is valid
3. Ensure the file has the `.agent.yaml` extension
4. Check file permissions

### Agent Won't Load

If an agent file is found but won't load:

1. Validate the YAML syntax using a YAML validator
2. Check that all mandatory fields are present: name, enabled, description, role, instructions
3. Verify tool names are correct and available
4. Check the QX logs for detailed error messages

### Agent Behaves Unexpectedly

If an agent doesn't behave as expected:

1. Review the role and instructions for clarity
2. Check if conflicting guidelines exist
3. Verify the model configuration is appropriate
4. Test with a simpler configuration first

## Advanced Topics

### Environment Variables

#### QX Agent Variables

**Core Agent Selection:**
- **QX_DEFAULT_AGENT**: Sets which agent to load on startup (default: "qx")

**Agent Context:**
- **QX_USER_CONTEXT**: User context passed to agent templates
- **QX_PROJECT_CONTEXT**: Project context passed to agent templates  
- **QX_PROJECT_FILES**: Project file listing passed to agent templates

**Agent Defaults Configuration:**
- **QX_AGENT_NAME**: Default agent name (default: "qx_agent")
- **QX_AGENT_VERSION**: Default agent version (default: "1.0.0")
- **QX_AGENT_DESCRIPTION**: Default agent description (default: "QX Agent")
- **QX_AGENT_TOOLS**: Default tools (comma-separated, default: none)
- **QX_AGENT_CONTEXT**: Default context template (default: none)
- **QX_AGENT_OUTPUT**: Default output formatting (default: none)

**Model Parameters:**
- **QX_AGENT_TEMPERATURE**: Model creativity (0.0-2.0, default: 0.73)
- **QX_AGENT_MAX_TOKENS**: Maximum response length (default: 4096)
- **QX_AGENT_TOP_P**: Nucleus sampling (0.0-1.0, default: 1.0)
- **QX_AGENT_FREQUENCY_PENALTY**: Repetition penalty (-2.0 to 2.0, default: 0.0)
- **QX_AGENT_PRESENCE_PENALTY**: Topic diversity (-2.0 to 2.0, default: 0.0)
- **QX_AGENT_REASONING_BUDGET**: Reasoning effort (none/low/medium/high, default: medium)

**Execution Settings:**
- **QX_AGENT_EXECUTION_MODE**: Default mode (interactive/autonomous/hybrid, default: interactive)
- **QX_AGENT_MAX_EXECUTION_TIME**: Task timeout seconds (default: 300)
- **QX_AGENT_MAX_ITERATIONS**: Maximum iterations per task (default: 10)
- **QX_AGENT_MAX_TOOL_CALLS**: Tool calls per turn (default: 10)

**Security Constraints:**
- **QX_AGENT_MAX_FILE_SIZE**: Maximum file size (default: "10MB")
- **QX_AGENT_ALLOWED_PATHS**: Allowed paths (comma-separated, default: "./")
- **QX_AGENT_FORBIDDEN_PATHS**: Forbidden paths (comma-separated, default: "/etc,/sys,/proc")
- **QX_AGENT_APPROVAL_REQUIRED_TOOLS**: Tools requiring approval (comma-separated, default: none)

**Console Configuration:**
- **QX_AGENT_USE_CONSOLE_MANAGER**: Use console manager (true/false, default: true)
- **QX_AGENT_SOURCE_IDENTIFIER**: Agent identifier in output (default: none)
- **QX_AGENT_ENABLE_RICH_OUTPUT**: Rich text formatting (true/false, default: true)
- **QX_AGENT_LOG_INTERACTIONS**: Log interactions (true/false, default: true)

**Autonomous Agent Settings:**
- **QX_AGENT_AUTONOMOUS_ENABLED**: Enable autonomous features (true/false, default: false)
- **QX_AGENT_MAX_CONCURRENT_TASKS**: Max concurrent tasks (1-10, default: 1)
- **QX_AGENT_TASK_TIMEOUT**: Task timeout seconds (default: 600)
- **QX_AGENT_HEARTBEAT_INTERVAL**: Heartbeat interval seconds (default: 30)
- **QX_AGENT_AUTO_RESTART**: Auto-restart failed agents (true/false, default: false)
- **QX_AGENT_POLL_INTERVAL**: Polling interval seconds (default: 5)

**Examples:**
```bash
# Basic agent configuration
export QX_DEFAULT_AGENT=code_reviewer
export QX_USER_CONTEXT="Senior Python developer working on data analysis tools"
export QX_PROJECT_CONTEXT="Flask web application with PostgreSQL backend"

# Security-focused setup
export QX_AGENT_TEMPERATURE=0.3
export QX_AGENT_ALLOWED_PATHS="./src,./docs,./tests"
export QX_AGENT_APPROVAL_REQUIRED_TOOLS="execute_shell_tool,write_file_tool"

# Autonomous development setup
export QX_AGENT_EXECUTION_MODE=autonomous
export QX_AGENT_AUTONOMOUS_ENABLED=true
export QX_AGENT_MAX_CONCURRENT_TASKS=3
export QX_AGENT_AUTO_RESTART=true

qx
```

#### Agent Configuration Variables

You can use environment variables in agent configurations:

```yaml
model:
  name: ${QX_MODEL_NAME}
  parameters:
    temperature: ${QX_TEMPERATURE:0.7}
```

### Agent Inheritance

Agents can reference and extend other agents (advanced feature - see developer documentation).

### Custom Tools

You can create custom tools for specific agents (see TOOL_DEVELOPMENT.md).

## Command Reference

| Command | Description |
|---------|-------------|
| `/agents` | List all available agents |
| `/agents list` | List all available agents (same as above) |
| `/agents switch <name>` | Switch to the specified agent |
| `/agents info` | Show current agent information |
| `/agents reload [name]` | Reload agent configuration from disk |
| `/agents refresh` | Refresh agent discovery (find new project agents) |

## Examples

### Switching to Code Review Mode

```
/agents switch code_reviewer
```

Now ask the agent to review your code:
```
Please review the changes in my latest commit for security issues and code quality.
```

### Working with Project Agents

```bash
# List agents (project agents will be highlighted)
/agents list

# Switch to a project-specific agent
/agents switch my_web_app_agent

# Ask project-specific questions
How should I structure the new user authentication feature in this codebase?

# Create a new component following project patterns
Create a new UserProfile component that follows our existing patterns
```

### Creating a Custom Documentation Agent

Create `docs_agent.agent.yaml`:

```yaml
name: "Documentation Agent"
enabled: true
description: "Technical documentation specialist"
role: |
  You are a technical documentation specialist who excels at creating clear,
  comprehensive documentation for software projects.

instructions: |
  ## Mission
  Create and maintain high-quality documentation that helps users and developers
  understand and use software effectively.
  
  ## Guidelines
  - Write in clear, accessible language
  - Include practical examples
  - Structure information logically
  - Keep documentation up to date with code changes

tools: [
  read_file_tool,
  write_file_tool,
  web_fetch_tool
]

model:
  name: openrouter/anthropic/claude-3.5-sonnet
  parameters:
    temperature: 0.3
    max_tokens: 8192
```

Then switch to it:
```
/agents switch docs_agent
```

### Project-Specific Agent Examples

#### Web Development Project Agent

Create `.Q/agents/web_dev.agent.yaml` for a React/Node.js project:

```yaml
name: "Web Dev Specialist"
enabled: true
description: "Full-stack web development specialist for React/Node.js projects"
role: |
  You are a full-stack web development specialist for this React/Node.js project.
  You understand modern web development practices and this project's architecture.

instructions: |
  ## Project Context
  This is a React frontend with Node.js backend project.
  
  ## Your Expertise
  - React components and hooks
  - Node.js/Express backend development
  - TypeScript/JavaScript best practices
  - Project-specific patterns and conventions
  
  ## Guidelines
  - Follow the existing code style and patterns
  - Use TypeScript when appropriate
  - Consider performance and accessibility
  - Write tests for new functionality

tools: [
  read_file_tool,
  write_file_tool,
  execute_shell_tool
]

model:
  name: openrouter/anthropic/claude-3.5-sonnet
  parameters:
    temperature: 0.7
```

#### Data Science Project Agent

Create `.Q/agents/data_scientist.agent.yaml` for a Python data project:

```yaml
name: "Data Scientist"
enabled: true
description: "Data scientist specializing in Python data analysis projects"
role: |
  You are a data scientist specializing in this Python data analysis project.
  You understand the project's data sources, analysis goals, and methodology.

instructions: |
  ## Project Context
  This project analyzes {describe your data and goals}.
  
  ## Your Expertise
  - Python data stack (pandas, numpy, scikit-learn)
  - Statistical analysis and visualization
  - Project-specific data schemas and workflows
  - Jupyter notebook best practices
  
  ## Guidelines
  - Follow project naming conventions
  - Document analysis steps clearly
  - Use established data preprocessing pipelines
  - Create reproducible analyses

tools: [
  read_file_tool,
  write_file_tool,
  execute_shell_tool
]

model:
  name: openrouter/google/gemini-2.5-pro-preview-06-05
  parameters:
    temperature: 0.3
```

#### DevOps Project Agent

Create `.Q/agents/devops.agent.yaml` for infrastructure projects:

```yaml
name: "DevOps Engineer"
enabled: true
description: "DevOps engineer specializing in infrastructure projects"
role: |
  You are a DevOps engineer specializing in this infrastructure project.
  You understand the deployment pipeline, monitoring, and operational requirements.

instructions: |
  ## Project Context
  This project manages infrastructure using {your stack: Kubernetes, Terraform, etc.}.
  
  ## Your Expertise
  - Infrastructure as Code (Terraform, CloudFormation)
  - Container orchestration (Kubernetes, Docker)
  - CI/CD pipeline optimization
  - Monitoring and alerting setup
  - Security and compliance
  
  ## Guidelines
  - Follow infrastructure security best practices
  - Use project's established patterns
  - Document infrastructure changes
  - Consider cost optimization

tools: [
  read_file_tool,
  write_file_tool,
  execute_shell_tool
]

model:
  name: openrouter/anthropic/claude-3.5-sonnet
  parameters:
    temperature: 0.5
```

## Project Agent Workflow

Here's a typical workflow for using project agents:

1. **Navigate to your project directory**:
   ```bash
   cd /path/to/your/project
   ```

2. **Start QX** (it will automatically discover any existing project agents):
   ```bash
   qx
   ```

3. **List available agents** (project agents will be highlighted):
   ```
   /agents list
   ```

4. **Create a new project agent** if needed:
   ```bash
   # Create the directory if it doesn't exist
   mkdir -p .Q/agents
   
   # Create your agent file
   vim .Q/agents/my_project_agent.agent.yaml
   ```

5. **Refresh discovery** to pick up the new agent:
   ```
   /agents refresh
   ```

6. **Switch to your project agent**:
   ```
   /agents switch my_project_agent
   ```

7. **Start working** with context-aware assistance!

## Getting Help

- Use `/help` to see all available commands
- Check the QX logs if agents aren't working as expected
- Refer to the developer documentation for advanced configuration options
- Look at the built-in agent configurations as examples