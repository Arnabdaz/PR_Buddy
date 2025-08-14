# 📜 PR Buddy AI Rules for Cursor

This directory contains AI-powered rules that enhance Cursor's Agent Mode with intelligent PR management capabilities.

## 🎯 Overview

These rules work in conjunction with the PR Buddy MCP servers to provide comprehensive PR lifecycle management directly within Cursor IDE. When installed globally (`~/.cursor/rules/`), they're available across all your projects.

## 📋 Available Rules

### 1. `pr-creation.mdc` - PR Creation Assistant

**Purpose:** Streamlines the creation of high-quality pull requests with proper context and documentation.

**Key Features:**

- Pre-creation review of changes
- Automatic Jira ticket integration
- Smart PR title and description generation
- Branch validation and setup
- Conflict detection before creation
- Test evidence inclusion

**Activation:** Triggered when you mention creating a PR or preparing changes for review.

**Example Commands:**

```
@agent Create a PR for my authentication changes
@agent Prepare a pull request for the feature/oauth branch
@agent I need to create a PR for DSE-1234
```

### 2. `pr-review.mdc` - PR Review Assistant

**Purpose:** Performs comprehensive PR reviews with security scanning and bug detection.

**Key Features:**

- Multi-aspect code review (bugs, security, performance)
- CVE vulnerability scanning
- Jira requirement compliance checking
- Actionable feedback generation
- Review comment formatting
- Priority-based issue reporting

**Activation:** Triggered when you request a PR review or analysis.

**Example Commands:**

```
@agent Review PR #123 for security issues
@agent Analyze the pull request for bugs
@agent Check PR #456 for CVE vulnerabilities
```

### 3. `pr-update.mdc` - PR Update Assistant

**Purpose:** Safely updates existing PRs while preserving important content.

**Key Features:**

- Smart description enhancement
- Jira requirement synchronization
- Test evidence preservation
- Comment and review retention
- Changelog generation
- Safe metadata updates

**Activation:** Triggered when you need to update or modify an existing PR.

**Example Commands:**

```
@agent Update PR #789 description with latest Jira requirements
@agent Add test results to PR #321
@agent Sync PR #654 with the latest ticket information
```

## 🚀 Installation

### Global Installation (Recommended)

Install rules globally to have them available in all projects:

```bash
# Create Cursor's global rules directory
mkdir -p ~/.cursor/rules

# Copy all PR Buddy rules
cp *.mdc ~/.cursor/rules/

# Verify installation
ls -la ~/.cursor/rules/pr-*.mdc
```

### Project-Specific Installation

For project-specific customization:

```bash
# Create project rules directory
mkdir -p .cursor/rules

# Copy specific rules
cp pr-review.mdc .cursor/rules/
```

## 🔧 How Rules Work

### Rule Loading Order

1. **Project rules** (`.cursor/rules/`) - Highest priority
2. **Global rules** (`~/.cursor/rules/`) - Default rules
3. **Built-in Cursor rules** - Lowest priority

### Rule Activation

Rules are automatically activated based on:

- Keywords in your message (create, review, update, PR, pull request)
- Context from your current workspace
- Active files and recent changes
- MCP server availability

### Integration with MCP Servers

The rules interact with:

- **Git Server**: Branch management, diff generation
- **GitHub Server**: PR operations, API interactions
- **Jira Server**: Ticket retrieval, requirement sync
- **CVE Server**: Security vulnerability scanning

## 📝 Customization

You can customize rules by editing the `.mdc` files:

### Modify Behavior

```markdown
# In pr-review.mdc

- Focus more on performance issues
- Add custom linting rules
- Adjust severity thresholds
```

### Add Project-Specific Checks

```markdown
# Create custom-pr-review.mdc

- Include company-specific compliance checks
- Add team coding standards
- Integrate with internal tools
```

## 🎭 Rule Interaction Examples

### Complete PR Workflow

```bash
# 1. Create a feature branch and make changes
git checkout -b feature/new-auth

# 2. Create PR with AI assistance
@agent Create a PR for my authentication changes linked to DSE-1234

# 3. Review the PR
@agent Review my PR for security issues and bugs

# 4. Update based on feedback
@agent Update the PR description with the review findings
```

### Cross-Team Collaboration

```bash
# Review a colleague's PR
@agent Review PR #456 focusing on API compatibility

# Add comprehensive feedback
@agent Generate detailed review comments for PR #456

# Suggest improvements
@agent What optimizations could improve PR #456?
```

## 🛠️ Troubleshooting

### Rules Not Activating

1. Check if rules are in the correct directory
2. Restart Cursor after adding rules
3. Ensure Agent Mode is enabled
4. Verify MCP servers are running

### Conflicts with Other Rules

- Rename rules to adjust priority (alphabetical loading)
- Use project-specific overrides
- Disable conflicting global rules

### Performance Issues

- Rules are lightweight and shouldn't impact performance
- If slow, check MCP server connections
- Reduce rule complexity for large codebases

## 📊 Best Practices

1. **Keep Rules Updated**

   ```bash
   cd /path/to/pr-buddy
   git pull
   cp rules/*.mdc ~/.cursor/rules/
   ```

2. **Backup Custom Rules**

   ```bash
   cp -r ~/.cursor/rules ~/.cursor/rules.backup
   ```

3. **Test Rules in Isolation**

   - Create a test project
   - Copy one rule at a time
   - Verify expected behavior

4. **Monitor Rule Performance**
   - Check Cursor's console for errors
   - Review MCP server logs
   - Track rule activation patterns

## 🔗 Related Documentation

- [PR Buddy Main Documentation](../README.md)
- [Quick Reference Guide](../QUICK_REFERENCE.md)
- [MCP Server Setup](../servers/README.md)
- [Cursor AI Documentation](https://docs.cursor.com)

## 📄 License

These rules are part of the PR Buddy project and are distributed under the MIT License.

---

**Need Help?** Check the main PR Buddy documentation or open an issue in the repository.
