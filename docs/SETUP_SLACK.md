# 💬 Slack Access Token Setup

This guide will help you create and configure a Slack token for PR Buddy integration.

## Why You Need a Slack Token

PR Buddy uses Slack integration to:

- Search public channels for prior discussion of a PR or Jira ticket
- Read message threads for context while reviewing or updating a PR
- List channels and resolve user IDs to names
- Post PR notifications and review alerts to a channel — always behind an explicit
  confirmation step (nothing is sent automatically)

## Prerequisites

- A Slack workspace
- Permission to create and install a Slack app in that workspace
- The ability to grant **User Token Scopes**

> **Important**: PR Buddy's Slack server authenticates with a **User OAuth Token**
> (`xoxp-...`), **not** a bot token (`xoxb-...`). This is required because Slack's
> `search.messages` API only accepts user tokens.

## Creating a Slack User Token

### Step 1: Create a Slack App

1. **Go to the Slack API dashboard**
   - Navigate to [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click **"Create New App"**
   - Choose **"From scratch"**
   - Name it `PR-Buddy` and select your workspace
   - Click **"Create App"**

### Step 2: Add User Token Scopes

1. In the left sidebar, open **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"User Token Scopes"** (not *Bot* Token Scopes)
3. Add exactly these five scopes:

   | Scope              | Enables                                             |
   | ------------------ | --------------------------------------------------- |
   | `search:read`      | Searching messages (`search_messages`)              |
   | `channels:history` | Reading channel history and threads                 |
   | `channels:read`    | Listing public channels and resolving channel names |
   | `users:read`       | Resolving user IDs to display names                 |
   | `chat:write`       | Posting messages (via the confirmation flow)        |

### Step 3: Install the App and Copy the Token

1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"** and approve the requested scopes
3. Copy the **"User OAuth Token"** — it starts with `xoxp-`
4. **⚠️ IMPORTANT**: Store it securely. Treat it like a password.

> Make sure you copy the **User** OAuth Token (`xoxp-...`), not the Bot User OAuth
> Token (`xoxb-...`). A bot token will fail on `search.messages`.

## Configuring the Token

### During Setup (Recommended)

When running `./setup_pr_buddy.sh`, you'll be prompted:

```bash
Slack User OAuth Token (xoxp-...): [paste your token here]
```

### Manual Configuration

1. **Edit the environment file**:

   ```bash
   nano ~/.pr-buddy/.env
   ```

2. **Add your Slack configuration**:

   ```bash
   # Slack Configuration
   SLACK_USER_TOKEN="xoxp-your-user-token-here"

   # Optional: how long a draft confirmation token stays valid (seconds, default 300)
   SLACK_DRAFT_TTL_SECONDS="300"
   ```

## Testing Your Slack Connection

### Quick Test

```bash
# Replace with your value
SLACK_USER_TOKEN="xoxp-your-user-token-here"

curl -s -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  https://slack.com/api/auth.test
```

### Expected Response

```json
{
  "ok": true,
  "url": "https://yourworkspace.slack.com/",
  "team": "Your Workspace",
  "user": "your.name",
  "team_id": "T01234567",
  "user_id": "U01234567"
}
```

If you see `{"ok": false, "error": "invalid_auth"}`, the token is wrong or revoked.

### Test Script

Save as `test_slack_connection.sh`:

```bash
#!/bin/bash

echo "Testing Slack Connection..."

# Use environment variable or command line argument
SLACK_USER_TOKEN="${SLACK_USER_TOKEN:-$1}"

if [ -z "$SLACK_USER_TOKEN" ]; then
    echo "❌ Missing configuration"
    echo "Usage: $0 <xoxp-token>"
    echo "Or set the environment variable: SLACK_USER_TOKEN"
    exit 1
fi

# Test authentication
response=$(curl -s -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  https://slack.com/api/auth.test)

if echo "$response" | grep -q '"ok":true'; then
    echo "✅ Connection successful!"
    echo "Team: $(echo "$response" | grep -o '"team":"[^"]*' | cut -d'"' -f4)"
    echo "User: $(echo "$response" | grep -o '"user":"[^"]*' | cut -d'"' -f4)"
else
    echo "❌ Connection failed"
    echo "Response: $response"
    echo ""
    echo "Common issues:"
    echo "- Ensure you copied the User OAuth Token (xoxp-...), not a bot token (xoxb-...)"
    echo "- Verify the app is installed to your workspace"
    echo "- Confirm all five User Token Scopes were granted"
fi
```

## Required OAuth Scopes

PR Buddy's Slack server needs these **User Token Scopes**:

- **`search:read`**: Search public-channel messages for PR/Jira context
- **`channels:history`**: Read channel history and full threads
- **`channels:read`**: List public channels and resolve names to IDs
- **`users:read`**: Resolve user IDs (e.g. `U01234567`) to display names
- **`chat:write`**: Post messages (only ever after explicit confirmation)

## What This Server Can and Cannot Do

**Can:**

- Search, list, and read **public** channels and their threads
- Resolve users
- Post to a **public** channel — but only through a two-step confirmation flow:
  `draft_message` returns a preview and a one-time confirmation token, and nothing is
  posted until `send_message` is called with that token.

**Cannot (refused server-side, regardless of token permissions):**

- Read or post to **direct messages**
- Read or post to **private channels**
- Read or post to **group DMs**

## Security Best Practices

### 1. Token Security

- Store tokens in environment variables, not code
- Never commit tokens to version control
- Use secure password managers

### 2. Token Rotation

- Rotate tokens periodically (e.g. every 90 days)
- Reinstall the app to regenerate the token, then update `~/.pr-buddy/.env`
- Keep a list of where tokens are used

### 3. Access Control

- Grant only the five scopes listed above — nothing more
- Consider a dedicated Slack account for the integration
- Review the app's authorized scopes regularly

### 4. Secure Storage Options

```bash
# Option 1: Environment variable
export SLACK_USER_TOKEN="xoxp-your-token"

# Option 2: Secure file with restricted permissions
echo "xoxp-your-token" > ~/.slack_token
chmod 600 ~/.slack_token

# Option 3: Password manager CLI (1Password example)
export SLACK_USER_TOKEN="$(op read op://Personal/Slack/token)"
```

## Troubleshooting

### Common Issues

1. **`invalid_auth` / `not_authed`**

   - Token is wrong, revoked, or not exported
   - You copied a bot token (`xoxb-...`) instead of a user token (`xoxp-...`)

2. **`missing_scope`**

   - A required User Token Scope was not granted
   - Add the missing scope under **OAuth & Permissions** and **reinstall** the app
     (scope changes require reinstalling)

3. **`channel_not_found` / channel refused**

   - The channel is private, a DM, or a group DM — only public channels are supported
   - The channel name/ID is incorrect, or your account is not a member of it

### Debug Commands

```bash
# Verify the token authenticates
curl -s -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  https://slack.com/api/auth.test

# List public channels the token can see
curl -s -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  "https://slack.com/api/conversations.list?types=public_channel" | jq '.channels[].name'

# Confirm search access (search:read scope)
curl -s -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  "https://slack.com/api/search.messages?query=test" | jq '.ok'
```

## Revoking Tokens

To revoke or rotate a Slack token:

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and open your PR-Buddy app
2. Under **OAuth & Permissions**, click **"Revoke All OAuth Tokens"** (or reinstall to rotate)
3. Reinstall the app to generate a fresh token, then update `~/.pr-buddy/.env`

## Next Steps

After setting up your Slack token:

1. Return to the [main README](../README.md#-complete-setup-guide) for installation
2. Test the integration by asking the agent to list Slack channels
3. Adjust `SLACK_DRAFT_TTL_SECONDS` if the default 5-minute confirmation window is too short
