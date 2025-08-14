# 🎫 Jira Access Token Setup

This guide will help you create and configure a Jira API token for PR Buddy integration.

## Why You Need a Jira Token

PR Buddy uses Jira integration to:

- Fetch ticket details and requirements automatically
- Link PRs to Jira tickets
- Update ticket status and add comments
- Verify acceptance criteria compliance
- Sync PR status with Jira workflow

## Prerequisites

- Jira Cloud account (Atlassian account)
- Access to at least one Jira project
- Permission to create API tokens

> **Note**: Jira Server/Data Center uses different authentication. This guide covers Jira Cloud.

## Creating a Jira API Token

### Step 1: Access API Token Settings

1. **Go to Atlassian Account Settings**
   - Navigate to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Or manually:
     - Go to any Jira Cloud page
     - Click your profile picture (top right)
     - Select "Manage account"
     - Click "Security" tab
     - Find "API tokens" section

### Step 2: Create New Token

1. Click **"Create API token"**
2. **Label your token**: `PR-Buddy-Integration`
3. Click **"Create"**
4. **⚠️ IMPORTANT**: Copy the token immediately! You won't be able to see it again.
5. Store it securely

### Step 3: Find Your Jira Base URL

Your Jira base URL is the address of your Jira instance:

- Format: `https://[your-domain].atlassian.net`
- Example: `https://mycompany.atlassian.net`

You can find it by:

1. Opening any Jira ticket
2. Looking at the browser address bar
3. Copying everything before `/browse/` or `/jira/`

## Configuring the Token

### During Setup (Recommended)

When running `./setup_pr_buddy.sh`, you'll be prompted:

```bash
Jira base URL (e.g., https://company.atlassian.net): [your URL]
Jira email: [your email]
Jira API token: [paste your token here]
```

### Manual Configuration

1. **Edit the environment file**:

   ```bash
   nano ~/.pr-buddy/.env
   ```

2. **Add your Jira configuration**:
   ```bash
   # Jira Configuration
   JIRA_BASE_URL="https://yourcompany.atlassian.net"
   JIRA_EMAIL="your-email@company.com"
   JIRA_API_TOKEN="your_jira_api_token_here"
   ```

## Testing Your Jira Connection

### Quick Test

```bash
# Replace with your values
JIRA_BASE_URL="https://yourcompany.atlassian.net"
JIRA_EMAIL="your-email@company.com"
JIRA_API_TOKEN="your_token_here"

curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself" \
  -H "Accept: application/json"
```

### Expected Response

```json
{
  "self": "https://yourcompany.atlassian.net/rest/api/3/user?accountId=...",
  "accountId": "5b10a2844...",
  "emailAddress": "your-email@company.com",
  "displayName": "Your Name",
  ...
}
```

### Test Script

Save as `test_jira_connection.sh`:

```bash
#!/bin/bash

echo "Testing Jira Connection..."

# Use environment variables or command line arguments
JIRA_BASE_URL="${JIRA_BASE_URL:-$1}"
JIRA_EMAIL="${JIRA_EMAIL:-$2}"
JIRA_API_TOKEN="${JIRA_API_TOKEN:-$3}"

if [ -z "$JIRA_BASE_URL" ] || [ -z "$JIRA_EMAIL" ] || [ -z "$JIRA_API_TOKEN" ]; then
    echo "❌ Missing configuration"
    echo "Usage: $0 <base_url> <email> <token>"
    echo "Or set environment variables: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN"
    exit 1
fi

# Test authentication
response=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself" \
  -H "Accept: application/json")

if echo "$response" | grep -q '"emailAddress"'; then
    echo "✅ Connection successful!"
    echo "User: $(echo "$response" | grep -o '"displayName":"[^"]*' | cut -d'"' -f4)"
    echo "Email: $(echo "$response" | grep -o '"emailAddress":"[^"]*' | cut -d'"' -f4)"

    # Test project access
    projects=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
      "$JIRA_BASE_URL/rest/api/3/project" \
      -H "Accept: application/json")

    project_count=$(echo "$projects" | grep -o '"key"' | wc -l)
    echo "Projects accessible: $project_count"
else
    echo "❌ Connection failed"
    echo "Response: $response"
    echo ""
    echo "Common issues:"
    echo "- Check your email and token are correct"
    echo "- Ensure the base URL is correct (e.g., https://company.atlassian.net)"
    echo "- Verify your account has API access enabled"
fi
```

## Common Jira Ticket Formats

PR Buddy recognizes these Jira ticket formats:

- `PROJ-123` - Standard format
- `DSE-1234` - Multiple digits
- `TEAM-45` - Different project keys

When creating PRs, reference tickets like:

```markdown
@pr-creation.mdc Create PR for PROJ-123 authentication feature
```

## Permissions Required

Your Jira account needs these permissions:

- **Browse Projects**: View projects and issues
- **View Issues**: Read issue details
- **Add Comments**: Post updates to tickets (optional)
- **Edit Issues**: Update ticket status (optional)

## Security Best Practices

### 1. Token Security

- Store tokens in environment variables, not code
- Never commit tokens to version control
- Use secure password managers

### 2. Token Rotation

- Rotate tokens every 90 days
- Delete old tokens after creating new ones
- Keep a list of where tokens are used

### 3. Access Control

- Use a dedicated service account if possible
- Grant minimal necessary permissions
- Review token usage regularly

### 4. Secure Storage Options

```bash
# Option 1: Environment variable
export JIRA_API_TOKEN="your_token"

# Option 2: Secure file with restricted permissions
echo "your_token" > ~/.jira_token
chmod 600 ~/.jira_token

# Option 3: Password manager CLI (1Password example)
export JIRA_API_TOKEN="$(op read op://Personal/Jira/token)"
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**

   - Wrong email or token
   - Token may be revoked
   - Account may be deactivated

2. **404 Not Found**

   - Incorrect base URL
   - API endpoint has changed
   - No access to the resource

3. **403 Forbidden**
   - Insufficient permissions
   - API access disabled for your account
   - Rate limiting

### Debug Commands

```bash
# Check if API is accessible
curl -I "$JIRA_BASE_URL/rest/api/3/myself"

# Verify authentication
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself" -v

# List accessible projects
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/project" \
  -H "Accept: application/json" | jq '.[] | .key'
```

## Revoking Tokens

To revoke a Jira API token:

1. Go to [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Find the token you want to revoke
3. Click "Revoke"
4. Confirm the action

## Jira Server/Data Center

If using self-hosted Jira (not Cloud):

1. **Authentication differs**: Uses username/password or Personal Access Tokens
2. **API endpoints differ**: Usually `/rest/api/2/` instead of `/rest/api/3/`
3. **Base URL format**: `https://jira.company.com` (no `.atlassian.net`)

Contact your Jira administrator for specific setup instructions.

## Next Steps

After setting up your Jira token:

1. Return to the [main README](../README.md#-complete-setup-guide) for installation
2. Test the integration with a sample ticket
3. Configure project-specific settings if needed
