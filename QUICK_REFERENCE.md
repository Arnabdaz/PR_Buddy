# 🚀 PR Buddy - Quick Reference Guide

## 📜 AI Rules Overview

PR Buddy includes three intelligent rules that enhance Cursor's Agent Mode:

| Rule            | File              | Purpose                         | Activation Keywords               |
| --------------- | ----------------- | ------------------------------- | --------------------------------- |
| **PR Creation** | `pr-creation.mdc` | Creates PRs with Jira context   | create, prepare, PR, pull request |
| **PR Review**   | `pr-review.mdc`   | Reviews PRs for bugs & security | review, analyze, check, scan      |
| **PR Update**   | `pr-update.mdc`   | Updates PR descriptions safely  | update, sync, modify, enhance     |

### Global Installation

```bash
# Install rules globally (available in all projects)
cp rules/*.mdc ~/.cursor/rules/
```

### Rule Capabilities

- **Automatic activation** based on intent
- **Context awareness** from workspace
- **MCP server integration** for operations
- **Intelligent decision making** for complex tasks

## 🎯 Quick Commands

### PR Creation

```markdown
@agent Create a PR from my changes
@agent Create a PR for feature/branch-name with Jira ticket DSE-1234
@agent Generate PR description from my staged changes
```

### PR Review

```markdown
@agent Review PR #123
@agent Review PR #456 for security vulnerabilities
@agent Check PR #789 for bugs and performance issues
@agent Scan PR #234 dependencies for CVEs
```

### PR Update

```markdown
@agent Update PR #567 description
@agent Sync PR #890 with latest Jira requirements
@agent Fix PR #345 checklist items
```

## 🛠️ MCP Tool Reference

### Git Operations (`mcp_git_*`)

| Tool                | Purpose                   | Example                              |
| ------------------- | ------------------------- | ------------------------------------ |
| `git_status`        | Check working tree status | "Show git status"                    |
| `git_diff`          | View changes              | "Show diff for main branch"          |
| `git_commit`        | Create commits            | "Commit with message 'Fix auth bug'" |
| `git_create_branch` | Create new branch         | "Create feature/new-feature branch"  |
| `git_push`          | Push to remote            | "Push to origin"                     |

### GitHub Operations (`mcp_github_*`)

| Tool                   | Purpose        | Example                          |
| ---------------------- | -------------- | -------------------------------- |
| `create_pull_request`  | Open new PR    | "Create PR from feature to main" |
| `get_pull_request`     | Get PR details | "Get details of PR #123"         |
| `merge_pull_request`   | Merge PR       | "Squash merge PR #456"           |
| `update_pull_request`  | Edit PR        | "Update PR #789 title"           |
| `search_pull_requests` | Find PRs       | "Find my open PRs"               |

### Jira Operations (`mcp_jira_*`)

| Tool                 | Purpose            | Example                |
| -------------------- | ------------------ | ---------------------- |
| `read_jira_issue`    | Get ticket details | "Read DSE-1234"        |
| `search_jira_issues` | Search tickets     | "Find my open tickets" |
| `add_jira_comment`   | Add comment        | "Comment on DSE-5678"  |
| `get_my_work`        | Get assigned work  | "Show my Jira tasks"   |

### CVE Operations (`mcp_cve_*`)

| Tool                            | Purpose                                  | Example                                         |
| ------------------------------- | ---------------------------------------- | ----------------------------------------------- |
| `check_dependencies`            | Vulnerable deps in a PR (exact versions) | "Check the dependencies this PR bumps"          |
| `check_package_vulnerabilities` | One package@version + fix version        | "Is log4j-core 2.14.1 vulnerable? What to use?" |
| `search_cve_by_id`              | Find specific CVE (fix, EPSS)            | "Check CVE-2021-44228"                          |
| `search_by_keyword`             | Search by tech                           | "Find React vulnerabilities"                    |
| `check_high_severity_cves`      | Get critical CVEs                        | "Show recent critical CVEs"                     |
| `get_recent_cves`               | Latest vulnerabilities                   | "CVEs from last 7 days"                         |

### Slack Operations (`mcp_slack_*`)

Public channels only. Posting is a two-step flow: `draft_message` returns a preview and a
one-time confirmation token, then `send_message` posts it — nothing is sent automatically.

| Tool                  | Purpose                          | Example                                  |
| --------------------- | -------------------------------- | ---------------------------------------- |
| `search_messages`     | Search public-channel messages   | "Search Slack for DSE-1234"              |
| `read_thread`         | Read a full thread with replies  | "Read that thread in #dev-reviews"       |
| `read_channel_history`| Read recent channel messages     | "Show recent #dev-reviews messages"      |
| `list_channels`       | List public channels             | "List Slack channels matching 'review'"  |
| `resolve_users`       | Resolve user IDs to names        | "Who is U01234567?"                      |
| `draft_message`       | Draft a message (returns token)  | "Draft a PR update note for #dev-reviews"|
| `send_message`        | Post a drafted message (confirm) | "Send it"                                |

## 📋 PR Template Structure

```markdown
## Description

[AI-generated comprehensive description]

Jira: DSE-XXXXX

## Checklist

- [x] No hardcoded credentials
- [x] Follows style conventions
- [x] Documentation updated
- [x] Tests added/updated
- [x] Guidelines followed
- [x] UI follows design system

## Blast Radius

[Affected components and impact]

## Manual Tests Conducted

[Evidence of testing]

---

**Review generated by AI**
[AI analysis summary]
```

## 🔍 JQL Quick Reference

### Common Queries

```jql
# Your work
assignee = currentUser() AND status != Done

# Recent updates
updated >= -7d ORDER BY updated DESC

# High priority
priority = High AND status = Open

# Sprint work
sprint in openSprints() AND project = PROJ

# Bugs
issuetype = Bug AND resolution = Unresolved
```

## ⚡ Keyboard Shortcuts (Cursor)

| Action            | Shortcut                    |
| ----------------- | --------------------------- |
| Open Agent Chat   | `Cmd+Shift+L`               |
| Toggle Agent Mode | `Cmd+Shift+A`               |
| Run PR Review     | `Cmd+Shift+P` → "PR Review" |
| Create PR         | `Cmd+Shift+P` → "PR Create" |

## 🚨 Safety Rules

### Branch Protection

- ❌ **NEVER** push directly to `master`/`main`
- ⚠️ **ALWAYS** confirm before force push
- ✅ **USE** feature branches for changes

### PR Operations

- 📝 **REVIEW** changes before PR creation
- 🔍 **ANALYZE** all findings before approval
- 💾 **PRESERVE** existing PR content on updates
- 🔐 **VERIFY** permissions before operations

## 📊 Status Indicators

### PR Review Severity Levels

- 🚨 **CRITICAL** - Security vulnerabilities, data loss risks
- ⚠️ **MAJOR** - Bugs, performance issues, breaking changes
- 📋 **MINOR** - Style issues, minor improvements
- 💡 **INFO** - Suggestions, best practices

### CVE Severity Scores

- **Critical** (9.0-10.0) - Immediate action required
- **High** (7.0-8.9) - Address urgently
- **Medium** (4.0-6.9) - Plan remediation
- **Low** (0.1-3.9) - Monitor and assess

## 🔧 Environment Variables

```bash
# Required
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."
export JIRA_BASE_URL="https://company.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="ATATT3xFfGF0..."

# Optional
export GITHUB_HOST="https://github.com"
export DEFAULT_GIT_REPO="/path/to/repo"
export SLACK_USER_TOKEN="xoxp-..."          # Slack user token (note: xoxp-, not xoxb-)
export SLACK_DRAFT_TTL_SECONDS="300"        # Draft confirmation window (default 300s)
export MCP_LOG_LEVEL="DEBUG"  # For troubleshooting
```

## 🐛 Quick Troubleshooting

| Issue                     | Quick Fix                     |
| ------------------------- | ----------------------------- |
| MCP server not responding | Restart Cursor, check logs    |
| Auth failure              | Verify tokens, check expiry   |
| PR creation fails         | Check branch protection rules |
| CVE scan timeout          | Reduce scope, retry           |
| Jira sync issues          | Verify API token permissions  |
| Slack search/send fails   | Use user token (xoxp-), check scopes; public channels only |

## 📝 Common Patterns

### Full PR Lifecycle

```markdown
1. @agent Create PR from feature/auth-oauth for DSE-1234
2. @agent Review my PR #123 thoroughly
3. @agent Update PR #123 based on review feedback
4. @agent Merge PR #123 using squash
```

### Security-First Review

```markdown
@agent Review PR #456 with focus on:

- Security vulnerabilities
- CVE scanning for all dependencies
- Authentication/authorization issues
- Data exposure risks
```

### Jira-Driven Development

```markdown
@agent Create PR that implements DSE-5678 requirements
@agent Verify PR #789 meets all DSE-5678 acceptance criteria
@agent Update PR #789 with latest DSE-5678 changes
```

## 🎭 Rules Management

### Check Installed Rules

```bash
# List global rules
ls -la ~/.cursor/rules/

# List project rules (if any)
ls -la .cursor/rules/
```

### Update Rules

```bash
# Pull latest from PR Buddy
cd /path/to/pr-buddy && git pull
cp rules/*.mdc ~/.cursor/rules/

# Restart Cursor to apply changes
```

### Manage Rules

```bash
# Disable rules temporarily
mv ~/.cursor/rules ~/.cursor/rules.backup

# Re-enable rules
mv ~/.cursor/rules.backup ~/.cursor/rules

# Remove specific rule
rm ~/.cursor/rules/pr-update.mdc

# Backup rules before updates
cp -r ~/.cursor/rules ~/.cursor/rules.$(date +%Y%m%d)
```

### Rule Loading Priority

1. **Project rules** (`.cursor/rules/`) - Highest priority, override global
2. **Global rules** (`~/.cursor/rules/`) - Default for all projects
3. **Built-in Cursor rules** - Lowest priority

### Rule Debugging

```bash
# Check if rules are loaded (in Cursor)
# Open Developer Tools: Help > Toggle Developer Tools
# Look for rule loading messages in Console

# Test rule activation
@agent test PR creation rule
@agent test PR review rule
@agent test PR update rule
```

---

💡 **Pro Tip**: Keep this guide open in a separate tab for quick reference while using PR Buddy!
