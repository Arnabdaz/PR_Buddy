# 🏗️ PR Buddy Architecture

This document provides a comprehensive overview of PR Buddy's architecture, components, and workflows.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Workflow Diagrams](#workflow-diagrams)
- [MCP Server Details](#mcp-server-details)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)

## System Overview

PR Buddy is built on the Model Context Protocol (MCP) architecture, integrating multiple specialized servers with AI-powered rules to create a comprehensive PR management system.

### High-Level Architecture

```mermaid
graph TB
    subgraph "PR Buddy System"
        subgraph "AI Rules Engine"
            PR_CREATE["📝 PR Creation Assistant<br/>• Pre-creation review<br/>• Jira context gathering<br/>• Description generation"]
            PR_REVIEW["🔍 PR Review Assistant<br/>• Bug detection<br/>• CVE scanning<br/>• Compliance checks"]
            PR_UPDATE["🔄 PR Update Assistant<br/>• Safe modifications<br/>• Content preservation<br/>• Smart enhancements"]
        end

        subgraph "MCP Servers"
            GIT["🗂️ Git Server<br/>• Local operations<br/>• Branch management<br/>• Commit handling"]
            GITHUB["🐙 GitHub Server<br/>• PR management<br/>• Issue tracking<br/>• Actions control"]
            JIRA["🎫 Jira Server<br/>• Ticket retrieval<br/>• Requirement sync<br/>• Comment posting"]
            CVE["🛡️ CVE Server<br/>• Vulnerability scan<br/>• Security alerts<br/>• Risk assessment"]
        end

        subgraph "Host Environment"
            CURSOR["💻 Cursor IDE<br/>• AI Agent Mode<br/>• MCP Integration<br/>• Code Context"]
        end
    end

    CURSOR --> PR_CREATE
    CURSOR --> PR_REVIEW
    CURSOR --> PR_UPDATE

    PR_CREATE --> GIT
    PR_CREATE --> GITHUB
    PR_CREATE --> JIRA

    PR_REVIEW --> GITHUB
    PR_REVIEW --> JIRA
    PR_REVIEW --> CVE

    PR_UPDATE --> GIT
    PR_UPDATE --> GITHUB
    PR_UPDATE --> JIRA

    style PR_CREATE fill:#4CAF50,stroke:#2E7D32,color:#fff
    style PR_REVIEW fill:#2196F3,stroke:#1565C0,color:#fff
    style PR_UPDATE fill:#FF9800,stroke:#E65100,color:#fff
    style CVE fill:#F44336,stroke:#C62828,color:#fff
```

## Component Architecture

### Core Components

```mermaid
graph LR
    subgraph "Frontend Layer"
        CURSOR_UI["Cursor IDE UI"]
        AGENT_MODE["Agent Mode Interface"]
    end

    subgraph "Rule Processing Layer"
        RULE_ENGINE["Rule Engine"]
        PR_RULES["PR Buddy Rules<br/>(.mdc files)"]
        CONTEXT["Context Manager"]
    end

    subgraph "MCP Layer"
        MCP_PROTOCOL["MCP Protocol Handler"]
        SERVER_MANAGER["Server Manager"]
    end

    subgraph "Server Layer"
        GIT_SRV["Git Server"]
        GITHUB_SRV["GitHub Server"]
        JIRA_SRV["Jira Server"]
        CVE_SRV["CVE Server"]
    end

    subgraph "External Services"
        GITHUB_API["GitHub API"]
        JIRA_API["Jira Cloud API"]
        CVE_DB["CVE Databases"]
        LOCAL_GIT["Local Git Repos"]
    end

    CURSOR_UI --> AGENT_MODE
    AGENT_MODE --> RULE_ENGINE
    RULE_ENGINE --> PR_RULES
    RULE_ENGINE --> CONTEXT
    CONTEXT --> MCP_PROTOCOL
    MCP_PROTOCOL --> SERVER_MANAGER

    SERVER_MANAGER --> GIT_SRV
    SERVER_MANAGER --> GITHUB_SRV
    SERVER_MANAGER --> JIRA_SRV
    SERVER_MANAGER --> CVE_SRV

    GIT_SRV --> LOCAL_GIT
    GITHUB_SRV --> GITHUB_API
    JIRA_SRV --> JIRA_API
    CVE_SRV --> CVE_DB

    style RULE_ENGINE fill:#4CAF50,stroke:#2E7D32,color:#fff
    style MCP_PROTOCOL fill:#2196F3,stroke:#1565C0,color:#fff
```

## Workflow Diagrams

### PR Creation Workflow

```mermaid
sequenceDiagram
    participant User
    participant Cursor
    participant PRBuddy
    participant Git
    participant GitHub
    participant Jira

    User->>Cursor: @pr-creation.mdc "Create PR"
    Cursor->>PRBuddy: Activate PR Creation Assistant
    PRBuddy->>Git: Check branch status
    Git-->>PRBuddy: Current branch info
    PRBuddy->>Git: Get uncommitted changes
    Git-->>PRBuddy: Diff/changes
    PRBuddy->>User: Present pre-creation review
    User->>PRBuddy: Approve/modify changes
    PRBuddy->>Git: Commit changes (if needed)
    PRBuddy->>Jira: Fetch ticket details
    Jira-->>PRBuddy: Ticket info & requirements
    PRBuddy->>PRBuddy: Generate PR description
    PRBuddy->>GitHub: Create pull request
    GitHub-->>PRBuddy: PR created (#123)
    PRBuddy->>Jira: Add PR link to ticket
    PRBuddy->>User: PR #123 created successfully
```

### PR Review Workflow

```mermaid
sequenceDiagram
    participant User
    participant Cursor
    participant PRBuddy
    participant GitHub
    participant CVE
    participant Jira

    User->>Cursor: @pr-review.mdc "Review PR #789"
    Cursor->>PRBuddy: Activate PR Review Assistant
    PRBuddy->>GitHub: Fetch PR details
    GitHub-->>PRBuddy: PR metadata
    PRBuddy->>GitHub: Get PR diff
    GitHub-->>PRBuddy: File changes

    par Security Scan
        PRBuddy->>CVE: Scan dependencies
        CVE-->>PRBuddy: Vulnerability report
    and Code Analysis
        PRBuddy->>PRBuddy: Analyze for bugs
        PRBuddy->>PRBuddy: Check patterns
    and Jira Verification
        PRBuddy->>Jira: Get linked tickets
        Jira-->>PRBuddy: Requirements
        PRBuddy->>PRBuddy: Verify compliance
    end

    PRBuddy->>PRBuddy: Compile review report
    PRBuddy->>User: Present findings
    User->>PRBuddy: Review decision

    opt Post Review
        PRBuddy->>GitHub: Post review comments
        PRBuddy->>GitHub: Set PR status
        PRBuddy->>Jira: Update ticket
    end
```

### PR Update Workflow

```mermaid
sequenceDiagram
    participant User
    participant Cursor
    participant PRBuddy
    participant Git
    participant GitHub
    participant Jira

    User->>Cursor: @pr-update.mdc "Update PR #456"
    Cursor->>PRBuddy: Activate PR Update Assistant
    PRBuddy->>GitHub: Fetch current PR
    GitHub-->>PRBuddy: PR details
    PRBuddy->>Jira: Get latest requirements
    Jira-->>PRBuddy: Updated ticket info
    PRBuddy->>PRBuddy: Analyze changes needed
    PRBuddy->>User: Propose updates
    User->>PRBuddy: Approve updates

    alt Update Description Only
        PRBuddy->>GitHub: Update PR description
    else Update Code
        PRBuddy->>Git: Make code changes
        PRBuddy->>Git: Commit & push
        PRBuddy->>GitHub: Update PR
    end

    PRBuddy->>Jira: Sync status
    PRBuddy->>User: PR updated successfully
```

## MCP Server Details

### Server Specifications

```mermaid
graph TB
    subgraph "Git Server"
        GIT_LANG["Language: Python"]
        GIT_PROTO["Protocol: MCP/stdio"]
        GIT_OPS["Operations:<br/>• status<br/>• diff<br/>• commit<br/>• branch<br/>• log"]
    end

    subgraph "GitHub Server"
        GH_LANG["Language: Go"]
        GH_PROTO["Protocol: MCP/stdio"]
        GH_OPS["Operations:<br/>• PR CRUD<br/>• Issues<br/>• Actions<br/>• Reviews<br/>• Files"]
    end

    subgraph "Jira Server"
        JIRA_LANG["Language: Python"]
        JIRA_PROTO["Protocol: MCP/stdio"]
        JIRA_OPS["Operations:<br/>• Get issues<br/>• Search JQL<br/>• Comments<br/>• Transitions"]
    end

    subgraph "CVE Server"
        CVE_LANG["Language: Python"]
        CVE_PROTO["Protocol: MCP/stdio"]
        CVE_OPS["Operations:<br/>• Search CVE<br/>• Scan deps<br/>• Risk score<br/>• Alerts"]
    end
```

### Server Communication

Each MCP server communicates through:

- **Protocol**: JSON-RPC over stdio
- **Transport**: Process pipes
- **Encoding**: UTF-8
- **Message Format**: MCP standard

## Data Flow

### Request Processing Pipeline

```mermaid
graph LR
    subgraph "Input"
        USER_CMD["User Command<br/>@pr-*.mdc"]
    end

    subgraph "Processing"
        PARSE["Parse Intent"]
        ROUTE["Route to Rule"]
        EXEC["Execute Rule"]
        CALL["MCP Calls"]
    end

    subgraph "Servers"
        S1["Server 1"]
        S2["Server 2"]
        SN["Server N"]
    end

    subgraph "Output"
        RESULT["Formatted Result"]
        UI["Cursor UI"]
    end

    USER_CMD --> PARSE
    PARSE --> ROUTE
    ROUTE --> EXEC
    EXEC --> CALL
    CALL --> S1
    CALL --> S2
    CALL --> SN
    S1 --> RESULT
    S2 --> RESULT
    SN --> RESULT
    RESULT --> UI

    style EXEC fill:#4CAF50,stroke:#2E7D32,color:#fff
    style CALL fill:#2196F3,stroke:#1565C0,color:#fff
```

### State Management

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> RuleActivated: User invokes rule
    RuleActivated --> ContextGathering: Rule starts
    ContextGathering --> ServerCalling: Context ready
    ServerCalling --> Processing: Servers respond
    Processing --> ResultFormatting: Data processed
    ResultFormatting --> UserPresentation: Format complete
    UserPresentation --> WaitingForInput: Need user input
    UserPresentation --> Complete: No input needed
    WaitingForInput --> ServerCalling: User responds
    Complete --> Idle: Reset

    note right of ContextGathering
        Gather code context,
        git status, current PR
    end note

    note right of ServerCalling
        Parallel MCP calls to
        multiple servers
    end note
```

## Security Architecture

### Authentication Flow

```mermaid
graph TB
    subgraph "Credential Storage"
        ENV["Environment Variables"]
        CONFIG["Config Files"]
        KEYCHAIN["OS Keychain<br/>(optional)"]
    end

    subgraph "PR Buddy"
        AUTH["Auth Manager"]
        TOKEN_GH["GitHub Token"]
        TOKEN_JIRA["Jira Token"]
    end

    subgraph "External Services"
        GH_AUTH["GitHub Auth"]
        JIRA_AUTH["Jira Auth"]
    end

    ENV --> AUTH
    CONFIG --> AUTH
    KEYCHAIN --> AUTH

    AUTH --> TOKEN_GH
    AUTH --> TOKEN_JIRA

    TOKEN_GH --> GH_AUTH
    TOKEN_JIRA --> JIRA_AUTH

    style AUTH fill:#F44336,stroke:#C62828,color:#fff
```

### Security Layers

1. **Transport Security**

   - HTTPS for all external API calls
   - Local process isolation for MCP servers

2. **Authentication**

   - Personal Access Tokens (PAT) for GitHub
   - API tokens for Jira
   - No credentials in code or logs

3. **Authorization**

   - Respect repository permissions
   - Follow Jira project access controls
   - Minimal permission principle

4. **Data Protection**
   - Sensitive data masked in logs
   - Temporary files cleaned up
   - No persistent storage of secrets

## Performance Considerations

### Resource Allocation

```mermaid
graph LR
    subgraph "Resource Usage"
        CPU["CPU Usage<br/>• CVE: Low<br/>• Git: Low<br/>• GitHub: Medium<br/>• Jira: Low"]
        MEM["Memory<br/>• CVE: 100MB<br/>• Git: 50MB<br/>• GitHub: 200MB<br/>• Jira: 100MB"]
        NET["Network<br/>• CVE: API calls<br/>• Git: Local only<br/>• GitHub: REST/GraphQL<br/>• Jira: REST API"]
    end
```

### Optimization Strategies

1. **Parallel Processing**

   - Multiple MCP servers run concurrently
   - Async API calls where possible
   - Non-blocking UI operations

2. **Caching**

   - CVE results cached for 24 hours
   - Jira ticket data cached per session
   - GitHub metadata refreshed on demand

3. **Connection Pooling**

   - HTTP connection reuse
   - Persistent MCP server processes
   - Efficient stdio communication

4. **Selective Loading**
   - Load only required GitHub toolsets
   - Lazy initialization of servers
   - On-demand rule activation

### Performance Metrics

| Component              | Startup Time | Memory Usage | CPU Usage |
| ---------------------- | ------------ | ------------ | --------- |
| Git Server             | < 1s         | ~50MB        | Low       |
| GitHub Server (Go)     | < 2s         | ~200MB       | Medium    |
| GitHub Server (Docker) | 3-5s         | ~300MB       | Medium    |
| Jira Server            | < 1s         | ~100MB       | Low       |
| CVE Server             | < 2s         | ~100MB       | Low       |

## Scalability

### Horizontal Scaling

PR Buddy can scale through:

- Multiple concurrent PR operations
- Parallel server instances
- Distributed team usage

### Vertical Scaling

Performance improves with:

- More CPU cores (parallel processing)
- Additional RAM (larger PR handling)
- SSD storage (faster Git operations)

## Future Architecture Considerations

### Planned Enhancements

1. **WebSocket Support**

   - Real-time PR updates
   - Live collaboration features
   - Streaming logs

2. **Plugin Architecture**

   - Custom rule development
   - Third-party integrations
   - Extended server support

3. **Cloud Integration**

   - Remote server hosting
   - Shared configuration
   - Team synchronization

4. **AI Model Integration**
   - Local LLM support
   - Custom model fine-tuning
   - Enhanced code analysis

## Technical Stack

### Languages & Frameworks

- **Python 3.10+**: CVE, Git, and Jira servers
- **Go 1.21+**: GitHub server
- **TypeScript**: Cursor integration
- **JSON-RPC**: MCP communication

### Dependencies

- **UV**: Python package management
- **Docker**: Optional containerization
- **Git**: Version control operations
- **Cursor IDE**: Host environment

### External APIs

- **GitHub REST API v3**: Repository operations
- **GitHub GraphQL API v4**: Advanced queries
- **Jira REST API v3**: Issue management
- **CVE databases**: Multiple sources (NIST, MITRE, etc.)

## Debugging Architecture

### Logging Hierarchy

```mermaid
graph TD
    subgraph "Log Levels"
        DEBUG["DEBUG<br/>Detailed traces"]
        INFO["INFO<br/>Normal operations"]
        WARN["WARNING<br/>Potential issues"]
        ERROR["ERROR<br/>Failures"]
    end

    subgraph "Log Destinations"
        CONSOLE["Console Output"]
        FILE["Log Files"]
        CURSOR["Cursor Logs"]
    end

    DEBUG --> FILE
    INFO --> CONSOLE
    INFO --> FILE
    WARN --> CONSOLE
    WARN --> FILE
    WARN --> CURSOR
    ERROR --> CONSOLE
    ERROR --> FILE
    ERROR --> CURSOR
```

### Debug Flow

1. Enable debug mode in MCP config
2. Tail relevant log files
3. Use diagnostic scripts
4. Analyze server responses
5. Check external API status

## Conclusion

PR Buddy's architecture is designed for:

- **Modularity**: Independent, specialized servers
- **Extensibility**: Easy to add new capabilities
- **Reliability**: Fault-tolerant design
- **Performance**: Optimized for developer workflow
- **Security**: Multiple layers of protection

The architecture supports both current needs and future growth, ensuring PR Buddy remains a valuable tool for development teams.
