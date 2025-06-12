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

To reload agent configurations from disk:
```
/agents reload                # Reload ALL agents from disk
/agents reload [agent_name]   # Reload specific agent from disk
```

- **Without agent name**: Clears the entire agent cache and reloads all agent configurations from disk. This picks up any changes made to YAML files after QX was started.
- **With agent name**: Reloads only the specified agent's configuration from disk.

This is useful when you've modified agent YAML files and want QX to pick up the changes without restarting.

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
initial_query: "Hi! I'm ready to help with your coding tasks. What are you working on today?"
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
initial_query: "Hello! I'm here to help with documentation. What would you like me to write or update?"
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

## Complete Configuration Reference

For the comprehensive list of all available configuration options with detailed explanations, see the [Configuration Schema Reference](#configuration-schema-reference) section below.

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
  
  **Available Tools:**
  {discovered_tools}
  
  **Available Models:**
  {discovered_models}
  
  **Available Agents:**
  {discovered_agents}
```

#### Available Template Variables

- **`{user_context}`** - User context from QX_USER_CONTEXT environment variable
- **`{project_context}`** - Project context from QX_PROJECT_CONTEXT environment variable  
- **`{project_files}`** - Project file listing from QX_PROJECT_FILES environment variable
- **`{ignore_paths}`** - Contents of .gitignore file from current directory
- **`{agent_mode}`** - Current agent mode (single, supervisor, team_member)
- **`{current_agent_name}`** - Name of the current agent
- **`{team_context}`** - Team composition and context information
- **`{discovered_tools}`** - Complete documentation of all available tools (plugins + MCP)
- **`{discovered_models}`** - List of all available LLM models with descriptions
- **`{discovered_agents}`** - List of all discovered agents with descriptions

#### Using Template Variables

Template variables can be used in **any text field** of your agent configuration:

**In Instructions:**
```yaml
instructions: |
  You are a helpful assistant with access to various tools, models, and agents.
  
  ## Available Tools
  {discovered_tools}
  
  ## Available Models
  {discovered_models}
  
  ## Available Agents
  {discovered_agents}
  
  Use these tools, models, and agents appropriately to help users with their requests.
  You can switch to specialized agents when needed.
  Always explain which tools you're using and why.
```

**In Role:**
```yaml
role: |
  You are a specialist agent with access to these tools:
  {discovered_tools}
  
  Your expertise includes using these tools effectively to solve problems.
```

**In Context:**
```yaml
context: |
  ## Project Information
  **Project:** {project_context}
  **Files:** {project_files}
  
  ## Available Tools
  {discovered_tools}
  
  ## Team Context
  {team_context}
```

**In Output:**
```yaml
output: |
  When responding, remember you have access to:
  {discovered_tools}
  
  Format responses clearly and mention which tools you'll use.
```

**Multiple Locations:**
```yaml
role: |
  You are a development assistant with comprehensive tool access:
  {discovered_tools}

instructions: |
  Help users with coding tasks using the available tools:
  {discovered_tools}
  
  Always be explicit about your tool usage and reasoning.
```

#### Context Variable Formats

**Discovered Tools Format:**

The `{discovered_tools}` variable provides a simple list of available tools with descriptions:

```
- read_file_tool: Reads the contents of a file at a given path
- write_file_tool: Creates or updates a file with the provided content
- execute_shell_tool: Runs a specified command in the shell
- web_fetch_tool: Retrieves content from a URL
- current_time_tool: Provides the current date and time
- todo_manager_tool: Helps manage tasks and to-do lists
```

**Available Models Format:**

The `{discovered_models}` variable provides a simple list of available LLM models with their full identifiers and descriptions:

```
- openrouter/google/gemini-2.5-pro-preview-06-05: Preview 06-05 (OPENROUTER)
- openrouter/google/gemini-2.5-flash-preview-05-20: Preview 05-20 (OPENROUTER)
```

**Available Agents Format:**

The `{discovered_agents}` variable provides a simple list of all discovered agents with descriptions:

```
- qx: Main agent
- code_reviewer: Specialized code review and analysis agent
- devops_automation: DevOps automation and infrastructure management agent
- documentation_writer: Technical documentation and content creation specialist
- data_processor: Data analysis and processing automation agent
- qx.supervisor: Team supervisor and coordinator for multi-agent workflows
```

## Team Management

QX supports advanced multi-agent coordination through its team management system. You can create teams of specialized agents that work together on complex tasks, with automatic task decomposition and parallel execution.

### Team Management Commands

#### Creating and Building Teams

```bash
# Create a new empty team
/team-create frontend-specialists

# Add agents to your team
/team-add-member react_developer
/team-add-member ui_designer 2          # Add 2 instances for parallel work
/team-add-member code_reviewer

# View current team composition
/team-status

# Save your team for later use
/team-save frontend-specialists
```

#### Loading and Managing Saved Teams

```bash
# List all saved teams
/team-load                              # Shows available teams

# Load a specific team
/team-load frontend-specialists

# Remove agents from team
/team-remove-member ui_designer

# Clear entire team
/team-clear
```

#### Team Mode Control

```bash
# Enable team mode (multi-agent coordination)
/team-enable

# Disable team mode (single agent)
/team-disable

# Check current team mode status
/team-mode
```

### How Team Mode Works

When team mode is enabled and you have a team configured:

1. **Task Analysis**: The supervisor agent analyzes your request
2. **Task Decomposition**: Complex tasks are broken into parallelizable subtasks
3. **Agent Selection**: Best-suited agents are chosen based on their specializations
4. **Parallel Execution**: Subtasks run concurrently across agent instances
5. **Result Synthesis**: Multiple agent outputs are combined into unified responses

### Team Workflow Example

```bash
# Create and configure a code review team
/team-create code-review-team
/team-add-member code_reviewer
/team-add-member security_analyst
/team-add-member performance_optimizer
/team-save code-review-specialists

# Enable team coordination
/team-enable

# Now when you ask "Review my codebase for issues", QX will:
# - Analyze the request
# - Assign code quality to code_reviewer
# - Assign security analysis to security_analyst  
# - Assign performance review to performance_optimizer
# - Coordinate their work and synthesize results
```

### Team Storage

Teams are stored in:
- **Project-level**: `.Q/teams.json` (preferred, project-specific)
- **User-level**: `~/.config/qx/teams.json` (fallback)

The teams.json format stores all teams with their agent configurations and instance counts:

```json
{
  "teams": {
    "frontend-specialists": {
      "agents": {
        "react_developer": {"instance_count": 1},
        "ui_designer": {"instance_count": 2},
        "code_reviewer": {"instance_count": 1}
      },
      "saved_at": 1735776000,
      "version": "1.1"
    }
  },
  "version": "1.0"
}
```

### Agent Specializations

Agents can declare specializations to help the supervisor choose the right agent for each task:

```yaml
specializations:
  - "code_review"
  - "security_analysis" 
  - "performance_optimization"
```

Common specializations include:
- `code_review`, `security`, `performance`
- `frontend`, `backend`, `database`
- `documentation`, `testing`, `devops`
- `data_processing`, `automation`

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

## Configuration Schema Reference

This section provides a comprehensive guide to all available agent configuration options based on the schema definition in `/src/qx/core/schemas.py`.

### **Core Identity & Behavior**

#### **`name`** (str, required)
The human-readable display name for the agent that appears in UI elements, logs, and user interactions. This should be descriptive and unique within your agent collection. Examples: "Code Reviewer", "DevOps Specialist", "Data Analyst"

#### **`enabled`** (bool, required)
Controls whether the agent is available for selection and use. When set to `false`, the agent is discovered but cannot be switched to or executed. Useful for temporarily disabling agents without deleting their configuration files.

#### **`description`** (str, required)
A concise summary of the agent's purpose and capabilities, displayed in agent lists and help text. Should clearly communicate what the agent specializes in. Examples: "Specialized code review and security analysis agent", "Infrastructure automation and deployment specialist"

#### **`type`** (str, optional - default: "user")
Determines agent visibility in user interfaces. "user" agents appear in `/agents list` and UI selections, while "system" agents are hidden and used for internal operations like context compression or background processing.

#### **`version`** (str, optional - default: "1.0.0")
Semantic versioning for the agent configuration. Useful for tracking changes, compatibility, and rolling back configurations. Can be used by management systems to handle agent updates.

#### **`role`** (str, required)
Defines the agent's personality, expertise domain, and behavioral characteristics. This is the core identity that shapes how the agent responds. Should include domain expertise, communication style, and approach to problem-solving. Example: "You are a meticulous security-focused code reviewer with expertise in OWASP vulnerabilities and best practices."

#### **`instructions`** (str, required)
Detailed operational guidelines that specify exactly how the agent should behave, what processes to follow, and what outputs to produce. This is the most important configuration for agent behavior. Should include step-by-step workflows, quality standards, and specific methodologies.

#### **`context`** (str, optional)
Template string that gets prepended to the agent's prompt, containing runtime variables like `{user_context}`, `{project_context}`, `{discovered_tools}`. Used to inject dynamic information about the current environment, available resources, and user-specific context.

#### **`output`** (str, optional)
Guidelines for how the agent should format and structure its responses. Specifies output style, required sections, formatting preferences, and communication tone. Example: "Provide structured reports with Executive Summary, Detailed Findings, and Actionable Recommendations sections."

#### **`initial_query`** (str, optional)
An automatic greeting or initialization message that gets sent to the agent immediately when switching to it using `/agents switch <name>`. The initial query itself is not displayed to the user - only the agent's response is shown. This creates a welcoming, context-aware experience when switching agents. Example: "Hello! I'm ready to help with code reviews. What would you like me to analyze?" or "Hi! I'm here to assist with DevOps tasks. What infrastructure challenge can I help you solve today?"

### **Tool Access**

#### **`tools`** (List[str], optional - default: [])
Explicit list of tool names that the agent is permitted to use. If empty, agent has no tools. Tools must match exactly with available plugin/MCP tool names. Examples: `["read_file_tool", "write_file_tool", "execute_shell_tool"]`. Tool filtering provides security and prevents agents from accessing inappropriate functionality.

### **Model Configuration**

#### **`model.name`** (str, required)
The specific LLM model identifier to use for this agent. Must match available model names from the system's model registry. Examples: "openrouter/anthropic/claude-3.5-sonnet", "openrouter/google/gemini-2.5-pro-preview-06-05". Different models have different capabilities, costs, and response characteristics.

#### **`model.parameters.temperature`** (float, 0.0-2.0 - default: 0.73)
Controls response randomness and creativity. Lower values (0.1-0.3) produce more deterministic, focused responses ideal for code review or analysis. Higher values (0.7-1.0) encourage creative, varied responses better for brainstorming or content creation. Values above 1.0 can produce highly creative but potentially incoherent responses.

#### **`model.parameters.max_tokens`** (int, >0 - default: 4096)
Maximum number of tokens the model can generate in a single response. Longer responses cost more and take more time but allow for more comprehensive outputs. Set based on agent's typical response needs: 1024 for brief answers, 4096 for detailed analysis, 8192+ for comprehensive reports.

#### **`model.parameters.top_p`** (float, 0.0-1.0 - default: 1.0)
Nucleus sampling parameter that controls response diversity by limiting the cumulative probability of token choices. Lower values (0.1-0.5) focus on high-probability tokens for more predictable responses. Higher values (0.8-1.0) allow more diverse token selection for creative responses.

#### **`model.parameters.frequency_penalty`** (float, -2.0-2.0 - default: 0.0)
Reduces repetition by penalizing tokens based on their frequency in the response. Positive values discourage repetitive text, negative values encourage repetition. Useful for agents that tend to repeat phrases or concepts excessively.

#### **`model.parameters.presence_penalty`** (float, -2.0-2.0 - default: 0.0)
Encourages topic diversity by penalizing tokens that have already appeared, regardless of frequency. Positive values push the model to explore new topics and concepts, negative values encourage staying on established topics.

#### **`model.parameters.reasoning_budget`** (str - default: "medium")
For reasoning-capable models (like o1), controls how much computational effort to spend on reasoning before responding. "low" for quick responses, "medium" for balanced analysis, "high" for deep reasoning on complex problems. Affects response time and quality.

### **Execution Control**

#### **`max_execution_time`** (int, >0 - default: 300)
Maximum time in seconds that the agent can spend processing a single task before timing out. Prevents runaway processes and ensures responsive interactions. Set based on expected task complexity: 60s for simple queries, 300s for analysis tasks, 600s+ for complex operations.

#### **`max_iterations`** (int, >0 - default: 10)
Maximum number of tool-calling iterations the agent can perform in a single response cycle. Prevents infinite loops in tool usage while allowing complex multi-step operations. Higher values enable more sophisticated workflows but increase execution time and costs.

### **Execution Mode Configuration**

#### **`execution.mode`** (str - default: "interactive")
Determines how the agent operates: "interactive" for real-time conversation, "autonomous" for background task processing, "hybrid" for switching between modes. Interactive agents respond to user inputs, autonomous agents process queued tasks independently.

#### **`execution.autonomous_config.enabled`** (bool - default: false)
Enables autonomous operation capabilities, allowing the agent to process tasks from queues, run scheduled operations, and operate without direct user interaction. Required for background processing and automated workflows.

#### **`execution.autonomous_config.max_concurrent_tasks`** (int, 1-10 - default: 1)
Maximum number of tasks the agent can process simultaneously in autonomous mode. Higher values enable parallel processing but consume more resources. Set based on system capacity and task interdependencies.

#### **`execution.autonomous_config.task_timeout`** (int, >0 - default: 600)
Timeout for individual autonomous tasks in seconds. Longer than interactive timeout since autonomous tasks may be more complex. Should account for the most complex expected autonomous operations.

#### **`execution.autonomous_config.heartbeat_interval`** (int, >0 - default: 30)
Frequency in seconds for health check signals in autonomous mode. Shorter intervals provide better monitoring but increase overhead. Critical for detecting and recovering from agent failures in production environments.

#### **`execution.autonomous_config.auto_restart`** (bool - default: false)
Automatically restart the agent if it crashes or becomes unresponsive in autonomous mode. Essential for production systems but should be used carefully to avoid masking underlying issues that need fixing.

#### **`execution.autonomous_config.poll_interval`** (int, >0 - default: 5)
How frequently in seconds the agent checks for new tasks in autonomous mode. Shorter intervals provide faster response to new tasks but increase system load. Balance responsiveness needs with resource efficiency.

### **Security & Constraints**

#### **`execution.constraints.max_file_size`** (str - default: "10MB")
Maximum size of files the agent can read or write, specified with units (KB, MB, GB). Prevents agents from consuming excessive memory or processing huge files that could impact system performance. Set based on agent's legitimate file processing needs.

#### **`execution.constraints.allowed_paths`** (List[str] - default: ["./"])
File system paths where the agent is permitted to read/write files. Provides security by restricting agent access to appropriate directories. Use specific paths like `["./src", "./docs", "./tests"]` rather than broad access for security.

#### **`execution.constraints.forbidden_paths`** (List[str] - default: ["/etc", "/sys", "/proc"])
File system paths that are explicitly prohibited, even if they fall within allowed paths. Critical security feature to prevent access to system files, configuration directories, and sensitive locations.

#### **`execution.constraints.approval_required_tools`** (List[str] - default: [])
Tools that require explicit user approval before execution. Useful for potentially destructive operations like `execute_shell_tool` or `write_file_tool`. Provides an additional safety layer for high-risk operations.

#### **`execution.constraints.max_tool_calls_per_turn`** (int, >0 - default: 10)
Maximum number of tool calls the agent can make in a single response. Prevents excessive tool usage that could impact performance or costs while allowing reasonable multi-step operations.

### **Console & Output Management**

#### **`execution.console.use_console_manager`** (bool - default: true)
Enables the console management system for coordinated output handling, especially important in multi-agent environments. Provides better output formatting, prevents conflicts, and enables features like agent identification in output streams.

#### **`execution.console.source_identifier`** (str - default: none)
Custom identifier displayed in output to distinguish this agent's messages from others. Useful in multi-agent scenarios or when logging. Examples: "CodeReviewer", "DevOpsBot", "DataAnalyst".

#### **`execution.console.enable_rich_output`** (bool - default: true)
Enables rich text formatting with colors, styles, and advanced layouts. Disable for plain text environments or when rich formatting causes display issues. Rich output significantly improves readability and user experience.

#### **`execution.console.log_interactions`** (bool - default: true)
Controls whether agent conversations are logged to the system log files. Important for debugging, auditing, and analysis. Disable if logging creates performance issues or privacy concerns.

### **Lifecycle Hooks**

#### **`lifecycle.on_start`** (str - optional)
Message displayed or command executed when the agent starts. Can be a simple status message like "Starting comprehensive code review analysis..." or a command to execute. Useful for initialization feedback and setup operations.

#### **`lifecycle.on_task_received`** (str - optional)
Action triggered when the agent receives a new task in autonomous mode. Can log task receipt, perform setup operations, or notify monitoring systems. Important for task tracking and workflow automation.

#### **`lifecycle.on_error`** (str - optional)
Response to error conditions during agent operation. Can display helpful error messages, suggest troubleshooting steps, or trigger recovery procedures. Examples: "Code review error encountered. Checking for syntax issues and access permissions..."

#### **`lifecycle.on_shutdown`** (str - optional)
Action performed when the agent is shutting down. Can display completion summaries, clean up resources, or save state. Examples: "Code review session completed. Summary report generated."

### **Metadata & Organization**

#### **`created_at`** (str - optional)
ISO timestamp of when the agent configuration was created. Useful for tracking agent lifecycle, version management, and organizational purposes. Automatically managed by some systems.

#### **`updated_at`** (str - optional)
ISO timestamp of the last configuration modification. Important for change tracking, cache invalidation, and determining if agents need reloading. Should be updated whenever configuration changes.

#### **`tags`** (List[str] - default: [])
Classification labels for organizing and filtering agents. Examples: `["security", "code-review", "automation"]`, `["data", "analysis", "reporting"]`. Useful for agent discovery and management in large agent collections.

#### **`color`** (str - optional)
Hex color code for agent visual identification in UI elements and console output. Examples: "#ff5722" for orange, "#2196f3" for blue. Helps users quickly identify which agent is active or responding.

### **Special Features**

#### **`can_delegate`** (bool - default: false)
Enables the agent to delegate tasks to other specialized agents or switch to more appropriate agents based on task requirements. Critical for multi-agent workflows and intelligent task routing.

#### **`max_instances`** (int - optional)
Maximum number of concurrent instances of this agent that can run simultaneously. Prevents resource exhaustion while allowing reasonable parallelism. Useful for limiting resource-intensive agents or ensuring exclusive access to shared resources.

#### **`specializations`** (List[str] - optional)
Explicit list of the agent's expertise areas for automatic agent selection and routing. Examples: `["code_review", "security_analysis", "performance_analysis"]`. Used by supervisor agents to choose appropriate specialists for specific tasks.

### **Environment Variable Overrides**

Most configuration options can be overridden using environment variables with the `QX_AGENT_` prefix:

**Model Parameters:**
- `QX_AGENT_TEMPERATURE`
- `QX_AGENT_MAX_TOKENS`
- `QX_AGENT_TOP_P`
- `QX_AGENT_FREQUENCY_PENALTY`
- `QX_AGENT_PRESENCE_PENALTY`
- `QX_AGENT_REASONING_BUDGET`

**Execution Settings:**
- `QX_AGENT_EXECUTION_MODE`
- `QX_AGENT_MAX_EXECUTION_TIME`
- `QX_AGENT_MAX_ITERATIONS`
- `QX_AGENT_MAX_TOOL_CALLS`

**Autonomous Configuration:**
- `QX_AGENT_AUTONOMOUS_ENABLED`
- `QX_AGENT_MAX_CONCURRENT_TASKS`
- `QX_AGENT_TASK_TIMEOUT`
- `QX_AGENT_HEARTBEAT_INTERVAL`
- `QX_AGENT_AUTO_RESTART`
- `QX_AGENT_POLL_INTERVAL`

**Security Constraints:**
- `QX_AGENT_MAX_FILE_SIZE`
- `QX_AGENT_ALLOWED_PATHS`
- `QX_AGENT_FORBIDDEN_PATHS`
- `QX_AGENT_APPROVAL_REQUIRED_TOOLS`

**Console Configuration:**
- `QX_AGENT_USE_CONSOLE_MANAGER`
- `QX_AGENT_SOURCE_IDENTIFIER`
- `QX_AGENT_ENABLE_RICH_OUTPUT`
- `QX_AGENT_LOG_INTERACTIONS`

**Basic Configuration:**
- `QX_AGENT_VERSION`
- `QX_AGENT_CONTEXT`
- `QX_AGENT_OUTPUT`
- `QX_AGENT_TOOLS`

This comprehensive configuration system provides fine-grained control over every aspect of agent behavior, from basic personality and capabilities to advanced autonomous operation, security constraints, and multi-agent coordination.

## Getting Help

- Use `/help` to see all available commands
- Check the QX logs if agents aren't working as expected
- Refer to the developer documentation for advanced configuration options
- Look at the built-in agent configurations as examples