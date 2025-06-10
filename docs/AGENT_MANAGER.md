# Agent Manager - Modular Agent System for QX

## Overview

The Agent Manager is a comprehensive system for creating, managing, and executing modular agents in QX. It enables YAML-based agent configuration, dynamic agent switching, autonomous execution, and seamless integration with the existing console manager and plugin architecture.

## Architecture

### Core Components

1. **AgentLoader** - YAML configuration parsing and agent discovery
2. **AgentManager** - Agent lifecycle management and session coordination  
3. **AutonomousAgentRunner** - Independent thread execution for autonomous agents
4. **Agent Templates** - Pre-built specialized agents for different use cases
5. **Plugin Integration** - Tools for agent management through the existing plugin system

### Agent Configuration Schema

Agents are defined using YAML files with the following structure:

```yaml
# Basic agent metadata (mandatory fields)
name: "agent_name"           # Required: Display name
enabled: true               # Required: Whether agent is available
description: "Agent description"  # Required: Brief description
type: "user"               # Optional: "user" (default) or "system"
version: "1.0.0"           # Optional: Version number

# Core agent configuration (mandatory fields)
role: |
  Agent persona and context...
  
instructions: |
  Detailed operational guidelines...
  
context: |
  Template context with placeholders:
  {user_context}
  {project_context}
  {project_files}
  {ignore_paths}

output: |
  Response formatting guidelines...

# Available tools
tools: [
  read_file_tool,
  write_file_tool,
  execute_shell_tool
]

# Model configuration
model:
  name: openrouter/anthropic/claude-3.5-sonnet
  parameters:
    temperature: 0.7
    max_tokens: 4096
    reasoning_budget: medium

# Execution constraints
max_execution_time: 300
max_iterations: 10

# New modular agent capabilities
execution:
  mode: "interactive"  # interactive | autonomous | hybrid
  autonomous_config:
    enabled: false
    max_concurrent_tasks: 1
    task_timeout: 600
    heartbeat_interval: 30
    auto_restart: false
    poll_interval: 5
  constraints:
    max_file_size: "10MB"
    allowed_paths: ["./"]
    approval_required_tools: ["execute_shell_tool"]
  console:
    use_console_manager: true
    source_identifier: "AgentName"
    enable_rich_output: true

# Optional lifecycle hooks
lifecycle:
  on_start: "Agent initialization message..."
  on_task_received: "New task handling message..."
  on_error: "Error handling message..."
  on_shutdown: "Cleanup message..."
```

## Agent Discovery and Loading

### Search Paths

Agents are discovered in hierarchical order (lowest to highest priority):

1. **System agents**: `/etc/qx/agents/`
2. **User agents**: `~/.config/qx/agents/`
3. **Project agents**: `<project>/.Q/agents/`
4. **Local agents**: `./src/qx/agents/` (development)

### Agent File Naming

Agent files must follow the naming convention: `{agent_name}.agent.yaml`

Example: `code_reviewer.agent.yaml`, `devops_automation.agent.yaml`

### Agent Discovery Filtering

The agent loader provides several methods for discovering agents based on different criteria:

#### All Agents
```python
# Discover all agents regardless of type or enabled status
all_agents = loader.discover_agents()
```

#### User Agents Only
```python
# Discover only user-facing agents (excludes type="system")
user_agents = loader.discover_user_agents()
```

#### System Agents Only
```python
# Discover only system agents (type="system")
system_agents = loader.discover_system_agents()
```

#### Enabled Agents with Type Filtering
```python
# Discover all enabled agents
enabled_agents = loader.discover_enabled_agents()

# Discover only enabled user agents
enabled_user_agents = loader.discover_enabled_agents(agent_type="user")

# Discover only enabled system agents
enabled_system_agents = loader.discover_enabled_agents(agent_type="system")
```

### Agent Types

Agents are categorized by type to control their visibility and usage:

- **User Agents** (`type: "user"` or omitted): Regular agents shown in CLI/UI interfaces
- **System Agents** (`type: "system"`): Backend agents for internal processing, hidden from user interfaces

#### Use Cases for System Agents
- **Context Compression**: Summarizing large amounts of text for efficient processing
- **Data Transformation**: Background data processing and transformation tasks
- **Internal Operations**: System maintenance and optimization tasks
- **Pipeline Processing**: Automated workflow steps that don't require user interaction

#### Example System Agent Configuration
```yaml
name: "Context Compressor"
enabled: true
description: "System agent for compressing context information"
type: "system"
role: You are a context compression specialist.
instructions: |
  Compress large amounts of text while preserving key information.
  Focus on efficiency and accuracy.
tools: []
model:
  name: openrouter/google/gemini-2.5-flash-preview-05-20
  parameters:
    temperature: 0.1
```

### Template Context Injection

Agents support template placeholders that are replaced at runtime:

- `{user_context}` - User-specific context from environment
- `{project_context}` - Project-specific context
- `{project_files}` - Directory listing of project files
- `{ignore_paths}` - Contents of .gitignore file

## Usage

### Basic Agent Operations

#### List Available Agents

```bash
# Using the agent manager plugin tools
list_agents_tool --show_details true
```

#### Switch to Different Agent

```bash
# Switch to code review agent
switch_agent_tool --agent_name code_reviewer

# Switch and reload from disk
switch_agent_tool --agent_name code_reviewer --reload true
```

#### Get Agent Status

```bash
# Current agent status
agent_status_tool

# Include autonomous agents
agent_status_tool --include_autonomous true
```

#### Reload Agent Configuration

```bash
# Reload current agent
reload_agent_tool

# Reload specific agent
reload_agent_tool --agent_name devops_automation
```

### Autonomous Agent Operations

#### Start Autonomous Agent

```bash
# Start autonomous agent in background
start_autonomous_agent_tool --agent_name data_processor
```

#### Stop Autonomous Agent

```bash
# Stop running autonomous agent
stop_autonomous_agent_tool --agent_name data_processor
```

#### Add Tasks to Autonomous Agent

```bash
# Add task to autonomous agent queue
add_autonomous_task_tool \
  --agent_name data_processor \
  --description "Process daily sales data" \
  --content "Analyze sales data from ./data/sales.csv and generate summary report" \
  --priority high \
  --timeout 1800
```

## Agent Execution Modes

### Interactive Mode (Default)

- Agent responds to user input in real-time
- Uses existing QX interaction patterns
- Maintains backward compatibility

### Autonomous Mode

- Agent runs independently in background thread
- Processes task queues automatically
- Provides status updates through console manager
- Supports concurrent task execution

### Hybrid Mode

- Combines interactive and autonomous capabilities
- Can switch between modes based on context
- Supports both real-time interaction and background processing

## Built-in Agent Templates

### Main Agent (`qx.agent.yaml`)

The default QX agent that provides general software engineering and DevOps capabilities.

- **Focus**: General-purpose coding and DevOps tasks
- **Mode**: Interactive
- **Tools**: Full tool suite
- **Model**: High-capability model with reasoning

### Code Reviewer (`code_reviewer.agent.yaml`)

Specialized for comprehensive code review and analysis.

- **Focus**: Code quality, security, performance analysis
- **Mode**: Interactive
- **Specializations**: Static analysis, security auditing, best practices
- **Temperature**: Low (0.3) for consistent, analytical output

### DevOps Automation (`devops_automation.agent.yaml`)

Expert in infrastructure automation and deployment workflows.

- **Focus**: CI/CD, Infrastructure as Code, containerization
- **Mode**: Interactive + Autonomous capabilities
- **Specializations**: Pipeline design, cloud management, monitoring
- **Temperature**: Very low (0.2) for reliable automation

### Documentation Writer (`documentation_writer.agent.yaml`)

Specialized in creating technical documentation and user guides.

- **Focus**: Clear, comprehensive technical writing
- **Mode**: Interactive
- **Specializations**: API docs, user guides, architectural documentation
- **Temperature**: Moderate (0.4) for creative yet structured writing

### Data Processor (`data_processor.agent.yaml`)

Expert in data analysis, transformation, and automation.

- **Focus**: Statistical analysis, data pipelines, visualization
- **Mode**: Hybrid (interactive + autonomous)
- **Specializations**: ETL processes, data quality, performance optimization
- **Temperature**: Very low (0.1) for precise analytical work

## Integration with Existing Systems

### Console Manager Integration

All agents communicate through the existing console manager:

- **Thread Safety**: Concurrent agent operations without output conflicts
- **Source Identification**: Each agent has a unique source identifier
- **Rich Output**: Full support for Rich theming and formatting
- **Fallback Behavior**: Graceful degradation if console manager unavailable

### Plugin System Integration

The agent manager provides standard plugin tools:

- **Tool Discovery**: Automatic registration with plugin manager
- **Schema Generation**: Pydantic models for OpenAI function calling
- **Error Handling**: Structured error responses and logging
- **Approval Integration**: Uses existing approval handler for sensitive operations

### Session Management Integration

Agents integrate with existing session systems:

- **Session Persistence**: Agent context preserved across sessions
- **History Integration**: Agent interactions stored in session history
- **State Management**: Agent switching updates session state

### Security Integration

All security patterns are preserved and extended:

- **Path Validation**: Agent constraints respect existing security policies
- **Approval Requirements**: Tools requiring approval maintain existing behavior
- **Resource Limits**: Agent execution respects system resource constraints
- **Secrets Protection**: No agent configuration includes sensitive information

## Development

### Creating Custom Agents

1. **Create Agent File**: Add `{name}.agent.yaml` to appropriate agents directory
2. **Define Configuration**: Follow the agent schema with required fields
3. **Set Execution Mode**: Choose interactive, autonomous, or hybrid
4. **Configure Tools**: Specify required tools from available plugin tools
5. **Test Agent**: Use `reload_agent_tool` to test configuration changes

### Agent Configuration Best Practices

1. **Clear Role Definition**: Provide specific, focused agent personas
2. **Detailed Instructions**: Include comprehensive operational guidelines
3. **Appropriate Temperature**: Match temperature to task requirements
4. **Tool Selection**: Only include necessary tools for agent's purpose
5. **Resource Limits**: Set appropriate timeouts and iteration limits
6. **Security Constraints**: Define minimal required permissions

### Extending Autonomous Capabilities

To add autonomous task processing:

1. **Enable Autonomous Config**: Set `execution.autonomous_config.enabled: true`
2. **Configure Resources**: Set appropriate concurrency and timeout limits
3. **Define Task Handler**: Implement custom task processing logic
4. **Set Lifecycle Hooks**: Add appropriate startup, error, and shutdown handlers
5. **Monitor Performance**: Use heartbeat and status monitoring

## Monitoring and Debugging

### Agent Status Monitoring

```bash
# Get detailed agent status
agent_status_tool --include_autonomous true

# Monitor autonomous agent task history
# (Future enhancement: task history tool)
```

### Logging and Diagnostics

- **Agent Loading**: Detailed logs for configuration parsing and validation
- **Execution Monitoring**: Performance metrics and task processing stats
- **Error Tracking**: Comprehensive error logging with context
- **Console Integration**: Real-time status updates through console manager

### Performance Tuning

- **Task Concurrency**: Adjust `max_concurrent_tasks` for autonomous agents
- **Resource Limits**: Tune `max_file_size` and `max_tool_calls_per_turn`
- **Timeout Configuration**: Set appropriate `task_timeout` and `max_execution_time`
- **Poll Intervals**: Optimize `poll_interval` and `heartbeat_interval`

## Migration Guide

### From Legacy System

The agent system maintains full backward compatibility:

1. **Existing Workflows**: All current QX functionality continues unchanged
2. **Default Agent**: The `qx.agent.yaml` replaces the system prompt seamlessly
3. **Environment Variables**: All existing environment variables respected
4. **Plugin Tools**: No changes required for existing plugins

### Adopting Agent-Based Configuration

1. **Start with Default**: Use existing `qx.agent.yaml` as template
2. **Gradual Migration**: Create specialized agents for specific workflows
3. **Test Thoroughly**: Validate agent behavior with existing projects
4. **Monitor Performance**: Check resource usage with new agent configurations

## Troubleshooting

### Common Issues

#### Agent Not Found
- **Cause**: Agent file not in search paths or incorrect naming
- **Solution**: Check file location and ensure `.agent.yaml` suffix

#### Configuration Validation Errors
- **Cause**: Invalid YAML syntax or missing required fields
- **Solution**: Validate YAML syntax and check against schema

#### Template Context Errors
- **Cause**: Invalid template placeholders or context variables
- **Solution**: Verify placeholder names match available context

#### Tool Execution Failures
- **Cause**: Tools not available or permission issues
- **Solution**: Check tool registration and approval requirements

### Debugging Tips

1. **Check Logs**: Enable debug logging for detailed agent operations
2. **Validate Configuration**: Use YAML validators and schema checking
3. **Test Incrementally**: Start with simple agent configurations
4. **Monitor Resources**: Watch memory and CPU usage during execution
5. **Use Fallbacks**: Verify graceful degradation when systems unavailable

## Future Enhancements

### Planned Features

1. **Agent Templates**: GUI for creating agents from templates
2. **Task Scheduling**: Cron-like scheduling for autonomous agents
3. **Agent Marketplace**: Sharing and discovery of community agents
4. **Multi-Agent Coordination**: Workflows involving multiple agents
5. **Performance Analytics**: Detailed metrics and optimization suggestions

### Integration Opportunities

1. **External APIs**: Integration with external services and APIs
2. **Database Connectivity**: Direct database access for data agents
3. **Notification Systems**: Slack, email, and webhook integrations
4. **Version Control**: Git-based agent configuration management
5. **Cloud Deployment**: Containerized autonomous agent deployment

## Security Considerations

### Agent Isolation

- **Resource Limits**: Agents cannot exceed configured resource constraints
- **Path Restrictions**: File access limited to allowed paths
- **Tool Permissions**: Sensitive tools require approval
- **Network Access**: Web tools respect existing security policies

### Configuration Security

- **No Secrets**: Agent configurations must not contain API keys or passwords
- **Validation**: All agent configurations validated before loading
- **Audit Trail**: Agent operations logged for security monitoring
- **Rollback**: Ability to revert to previous agent configurations

### Autonomous Agent Security

- **Task Validation**: All autonomous tasks validated before execution
- **Timeout Protection**: Automatic termination of long-running tasks
- **Resource Monitoring**: Continuous monitoring of system resource usage
- **Emergency Stop**: Ability to immediately halt all autonomous agents

This modular agent system provides a powerful, flexible foundation for extending QX with specialized AI capabilities while maintaining the reliability, security, and user experience of the existing system.