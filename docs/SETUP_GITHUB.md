# 🔐 GitHub Access Token Setup

This guide will help you create and configure a GitHub Personal Access Token for PR Buddy.

## Why You Need a GitHub Token

PR Buddy needs a GitHub Personal Access Token to:

- Create and manage pull requests
- Review PR changes and post comments
- Access repository information
- Manage GitHub Actions workflows
- Perform security scans

## Creating a Personal Access Token

### For GitHub.com

1. **Navigate to Token Settings**

   - Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
   - Or manually: Click your profile picture → Settings → Developer settings → Personal access tokens

2. **Choose Token Type**

   - **Fine-grained tokens** (Recommended): More secure with specific repository access
   - **Classic tokens**: Simpler but broader access

3. **Create Fine-grained Token (Recommended)**

   - Click "Generate new token" → "Generate new token (Fine-grained)"
   - **Token name**: `PR-Buddy-Token`
   - **Expiration**: Choose based on your security policy (90 days recommended)
   - **Repository access**:

     - Select "Selected repositories" and choose your repositories
     - Or "All repositories" if you work across many repos

   - **Required Permissions**:

     ```
     Repository permissions:
     ✅ Actions: Read
     ✅ Contents: Read and Write
     ✅ Issues: Read and Write
     ✅ Metadata: Read
     ✅ Pull requests: Read and Write
     ✅ Commit statuses: Read

     Account permissions:
     ✅ Email addresses: Read (optional)
     ```

4. **Create Classic Token (Alternative)**

   - Click "Generate new token" → "Generate new token (Classic)"
   - **Note**: `PR-Buddy-Token`
   - **Expiration**: Choose based on your security policy
   - **Select scopes**:
     ```
     ✅ repo (Full control of private repositories)
     ✅ workflow (Update GitHub Action workflows)
     ✅ read:org (Read org and team membership)
     ```

5. **Generate and Save Token**
   - Click "Generate token"
   - **⚠️ IMPORTANT**: Copy the token immediately! You won't be able to see it again.
   - Token format: `ghp_xxxxxxxxxxxxxxxxxxxx`

### For GitHub Enterprise

1. **Navigate to Your Enterprise GitHub**

   - Go to `https://your-github-enterprise.com`
   - Click profile picture → Settings → Developer settings → Personal access tokens

2. **Create Token**
   - Follow the same steps as GitHub.com above
   - Ensure you have the correct enterprise URL for configuration

## Configuring the Token

### During Setup (Recommended)

When running `./setup_pr_buddy.sh`, you'll be prompted:

```bash
GitHub Personal Access Token (ghp_...): [paste your token here]
```

### Manual Configuration

1. **Edit the environment file**:

   ```bash
   nano ~/.pr-buddy/.env
   ```

2. **Add your token**:

   ```bash
   GITHUB_PERSONAL_ACCESS_TOKEN="ghp_your_token_here"
   GITHUB_HOST="https://github.com"  # or your enterprise URL
   ```

3. **For GitHub Enterprise**:
   ```bash
   GITHUB_PERSONAL_ACCESS_TOKEN="ghp_your_token_here"
   GITHUB_HOST="https://github.enterprise.company.com"
   ```

## Security Best Practices

### 1. Token Storage

- **Never** commit tokens to version control
- Use environment variables or secure vaults
- Consider using tools like 1Password CLI:
  ```bash
  export GITHUB_PERSONAL_ACCESS_TOKEN="$(op read op://Personal/GitHub/token)"
  ```

### 2. Token Rotation

- Set expiration dates (90 days recommended)
- Rotate tokens regularly
- Revoke old tokens after creating new ones

### 3. Minimal Permissions

- Use fine-grained tokens when possible
- Grant only necessary permissions
- Use separate tokens for different environments

### 4. Monitoring

- Review token usage in GitHub Settings
- Check audit logs for unusual activity
- Enable 2FA on your GitHub account

## Testing Your Token

### Quick Test

```bash
# For GitHub.com
curl -H "Authorization: token YOUR_TOKEN_HERE" \
  https://api.github.com/user

# For GitHub Enterprise
curl -H "Authorization: token YOUR_TOKEN_HERE" \
  https://your-github-enterprise.com/api/v3/user
```

### Expected Response

```json
{
  "login": "your-username",
  "id": 123456,
  "name": "Your Name",
  ...
}
```

## Troubleshooting

### Common Issues

1. **"Bad credentials" error**

   - Token may be expired or revoked
   - Check for typos in the token
   - Ensure no extra spaces or quotes

2. **"Not found" error**

   - Token lacks necessary permissions
   - Repository access not granted (for fine-grained tokens)

3. **"API rate limit exceeded"**
   - Token is working but hitting rate limits
   - Consider implementing caching or reducing API calls

### Token Validation Script

Save as `test_github_token.sh`:

```bash
#!/bin/bash

echo "Testing GitHub Token..."

TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN:-$1}"
HOST="${GITHUB_HOST:-https://github.com}"

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided"
    echo "Usage: $0 <token> or set GITHUB_PERSONAL_ACCESS_TOKEN"
    exit 1
fi

# Determine API endpoint
if [ "$HOST" = "https://github.com" ]; then
    API_URL="https://api.github.com"
else
    API_URL="$HOST/api/v3"
fi

# Test authentication
response=$(curl -s -H "Authorization: token $TOKEN" "$API_URL/user")

if echo "$response" | grep -q '"login"'; then
    echo "✅ Token is valid!"
    echo "User: $(echo "$response" | grep -o '"login":"[^"]*' | cut -d'"' -f4)"

    # Check rate limit
    rate_limit=$(curl -s -H "Authorization: token $TOKEN" "$API_URL/rate_limit")
    remaining=$(echo "$rate_limit" | grep -o '"remaining":[0-9]*' | head -1 | cut -d: -f2)
    echo "API calls remaining: $remaining/5000"
else
    echo "❌ Token validation failed"
    echo "Response: $response"
fi
```

## Revoking Tokens

If you need to revoke a token:

1. Go to [GitHub Settings → Personal access tokens](https://github.com/settings/tokens)
2. Find the token you want to revoke
3. Click "Delete" or "Revoke"
4. Confirm the action

## Next Steps

After setting up your GitHub token:

1. [Set up Jira Access Token](./SETUP_JIRA.md) (optional)
2. Return to the [main README](../README.md#-complete-setup-guide) for installation
