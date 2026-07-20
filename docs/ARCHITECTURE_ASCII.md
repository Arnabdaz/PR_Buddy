# PR Buddy Architecture (ASCII Version)

This document provides ASCII representations of the architecture diagrams for environments where Mermaid rendering is not available.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PR BUDDY SYSTEM                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────── AI RULES ENGINE ───────────────────────┐  │
│  │                                                               │  │
│  │  📝 PR Creation      🔍 PR Review        🔄 PR Update          │  │
│  │     Assistant           Assistant           Assistant         │  │
│  │  • Pre-review        • Bug detection     • Safe mods          │  │
│  │  • Jira context      • CVE scanning      • Content preserve   │  │
│  │  • PR generation     • Compliance        • Smart enhance      │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ▼                                      │
│  ┌──────────────────────── MCP SERVERS ──────────────────────────┐  │
│  │                                                               │  │
│  │  🗂️ Git Server       🐙 GitHub Server    🎫 Jira Server        │  │
│  │  • Local ops         • PR management     • Ticket retrieval   │  │
│  │  • Branch mgmt       • Issue tracking    • Requirement sync   │  │
│  │  • Commits           • Actions           • Comments           │  │
│  │                                                               │  │
│  │       🛡️ CVE Security Server      💬 Slack Server            │  │
│  │       • Vulnerability scanning     • Channel messaging        │  │
│  │       • Security alerts            • PR notifications          │  │
│  │       • Risk assessment            • Review alerts            │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ▲                                      │
│  ┌──────────────────── HOST ENVIRONMENT ─────────────────────────┐  │
│  │                                                               │  │
│  │                   💻 Cursor IDE                               │  │
│  │                 • AI Agent Mode                               │  │
│  │                 • MCP Integration                             │  │
│  │                 • Code Context                                │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## PR Creation Workflow

```
User                Cursor              PR Buddy            Git/GitHub/Jira
  │                   │                     │                      │
  ├──Request PR───────►                     │                      │
  │                   ├──Activate──────────►│                      │
  │                   │                     ├──Check status────────►
  │                   │                     ├──Get diff────────────►
  │                   │                     │                      │
  │◄──────────────────┼──Pre-review─────────┤                      │
  │                   │                     │                      │
  ├──Approve──────────►                     │                      │
  │                   │                     ├──Fetch Jira─────────►
  │                   │                     ├──Create PR──────────►
  │◄──────────────────┼──Success────────────┤                      │
  │                   │                     │                      │
```

## PR Review Workflow

```
User                Cursor              PR Buddy         GitHub/CVE/Jira
  │                   │                     │                      │
  ├──Review PR #123───►                     │                      │
  │                   ├──Activate──────────►│                      │
  │                   │                     ├──Fetch PR details────►
  │                   │                     ├──Scan CVEs──────────►
  │                   │                     ├──Check Jira─────────►
  │                   │                     │                      │
  │                   │                     ├─Analyze bugs─┐       │
  │                   │                     │              │       │
  │                   │                     ◄──────────────┘       │
  │                   │                     │                      │
  │◄──────────────────┼──Review report──────┤                      │
  │                   │                     │                      │
  ├──Decision─────────►                     │                      │
  │                   │                     ├──Post review────────►
  │                   │                     │                      │
```

## Resource Allocation

```
┌────────────────────────────────────────────────────────┐
│                  RESOURCE ALLOCATION                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  CPU Usage:           Memory:          Network:        │
│  ┌──────────┐        ┌───────────┐    ┌───────────┐    │
│  │ CVE: Low │        │ CVE: 100MB│    │ CVE: API  │    │
│  │ Git: Low │        │ Git: 50MB │    │ Git: Local│    │
│  │ GH: Med  │        │ GH: 200MB │    │ GH: API   │    │
│  │ Jira: Low│        │ Jira:100MB│    │ Jira: API │    │
│  └──────────┘        └───────────┘    └───────────┘    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Data Flow

```
                    ┌─────────────┐
                    │    USER     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   CURSOR    │
                    │  (AI Agent) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼────┐ ┌─────▼─────┐ ┌────▼─────┐
       │ PR CREATE │ │PR REVIEW  │ │PR UPDATE │
       │   RULE    │ │  RULE     │ │  RULE    │
       └──────┬────┘ └─────┬─────┘ └─────┬────┘
              │            │             │
              └────────────┼─────────────┘
                           │
         ┌─────────────────┼────────────────┐
         │                 │                │
    ┌────▼────┐      ┌─────▼────┐      ┌────▼────┐
    │   Git   │      │  GitHub  │      │  Jira   │
    │  Server │      │  Server  │      │  Server │
    └─────────┘      └──────────┘      └─────────┘
                           │
                     ┌─────▼────┐
                     │   CVE    │
                     │  Server  │
                     └──────────┘
```

---

**Note**: These ASCII diagrams are provided for compatibility. For the best viewing experience, please use the Mermaid diagrams in the main README with appropriate extensions installed.
