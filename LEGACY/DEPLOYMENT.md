# MCP Server Deployment Guide

This guide will help you deploy the MCP servers to your server environment with proper credential configuration.

## Prerequisites

- Python 3.10 or higher
- Git installed
- Access to your server environment
- Required API credentials (see sections below)

## Quick Start

1. **Clone the repository on your server:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/MCP_CREATOR.git
   cd MCP_CREATOR
   ```

2. **Set up credentials:**
   - Copy example files and add your actual credentials
   - See detailed instructions below for each service

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the MCP servers as needed**

---

## Credential Configuration

### Google MCP Server (Gmail, Drive, Calendar)

The Google MCP server requires OAuth 2.0 credentials.

**Step 1: Set up Google Cloud Console credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Google Drive API
   - Google Calendar API
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: Desktop app
   - Download the credentials JSON file

**Step 2: Create credentials.json**

```bash
cd mcp/google
cp credentials.json.example credentials.json
```

Edit `credentials.json` and replace the placeholders:
- `YOUR_CLIENT_ID` - Your OAuth client ID
- `your-project-id` - Your Google Cloud project ID
- `YOUR_CLIENT_SECRET` - Your OAuth client secret

Example:
```json
{
  "installed": {
    "client_id": "123456789-abc123xyz.apps.googleusercontent.com",
    "project_id": "my-mcp-project",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-AbC123XyZ...",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Step 3: Generate token.json (first-time authentication)**

The `token.json` file will be generated automatically on first run. Simply run the Google MCP server:

```bash
cd mcp/google
python server.py
```

You'll be prompted to authorize the application in your browser. After authorization, `token.json` will be created automatically.

**Note:** Keep both `credentials.json` and `token.json` secure. They are excluded from git by `.gitignore`.

---

### GitHub MCP Server

**Step 1: Generate a Personal Access Token**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "MCP Server")
4. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `user` (Read user profile data)
5. Generate and copy the token

**Step 2: Set environment variable**

```bash
export GITHUB_TOKEN="ghp_YourPersonalAccessToken123..."
```

Or add to your `.env` file (see Environment Variables section below).

---

### Slack MCP Server

**Step 1: Create a Slack App**

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Give it a name and select your workspace
4. Under "OAuth & Permissions", add these Bot Token Scopes:
   - `channels:history`
   - `channels:read`
   - `channels:write`
   - `chat:write`
   - `users:read`
   - `files:read`
5. Install the app to your workspace
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

**Step 2: Set environment variable**

```bash
export SLACK_BOT_TOKEN="xoxb-YourBotToken..."
```

---

### Todoist MCP Server

**Step 1: Get API Token**

1. Go to [Todoist Integrations](https://todoist.com/prefs/integrations)
2. Scroll to "API token" section
3. Copy your API token

**Step 2: Set environment variable**

```bash
export TODOIST_API_TOKEN="YourTodoistAPIToken..."
```

---

### Notion MCP Server

**Step 1: Create a Notion Integration**

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Give it a name and select the workspace
4. Copy the "Internal Integration Token"

**Step 2: Share databases with your integration**

1. Open the Notion database you want to access
2. Click "..." → "Add connections"
3. Select your integration

**Step 3: Set environment variable**

```bash
export NOTION_TOKEN="secret_YourNotionToken..."
```

---

### Home Assistant MCP Server

**Step 1: Generate Long-Lived Access Token**

1. In Home Assistant, go to your Profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Give it a name (e.g., "MCP Server")
5. Copy the token

**Step 2: Set environment variables**

```bash
export HA_URL="http://homeassistant.local:8123"
export HA_TOKEN="YourLongLivedAccessToken..."
```

---

### HYD_AGENT_MCP (Hydraulic Agent with Vision)

**Step 1: Get API Keys**

You need at least one of these:
- OpenAI API Key: [OpenAI Platform](https://platform.openai.com/api-keys)
- OpenRouter API Key: [OpenRouter](https://openrouter.ai/keys)

**Step 2: Database Setup**

If using PostgreSQL for memory:
1. Install PostgreSQL
2. Create a database: `createdb mcp_memory`

**Step 3: Set environment variables**

```bash
export OPENAI_API_KEY="sk-YourOpenAIKey..."
export OPENROUTER_API_KEY="sk-or-YourOpenRouterKey..."

# PostgreSQL (optional)
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="mcp_memory"
export POSTGRES_USER="your_db_user"
export POSTGRES_PASSWORD="your_db_password"
```

---

## Environment Variables Configuration

### Option 1: Using .env file (Recommended for deployment)

Create a `.env` file in the deployment directory:

```bash
cd deployment
cp .env.minimal.example .env
```

Edit `.env` and add your actual credentials. The file should look like:

```bash
# GitHub
GITHUB_TOKEN=ghp_YourGitHubToken...

# Todoist
TODOIST_API_TOKEN=YourTodoistToken...

# Home Assistant
HA_URL=http://homeassistant.local:8123
HA_TOKEN=YourHAToken...

# Notion
NOTION_TOKEN=secret_YourNotionToken...

# Slack
SLACK_BOT_TOKEN=xoxb-YourSlackToken...

# OpenAI (for HYD_AGENT_MCP)
OPENAI_API_KEY=sk-YourOpenAIKey...

# PostgreSQL (if using)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mcp_memory
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

Load the environment variables:
```bash
export $(cat .env | xargs)
```

### Option 2: System environment variables

Add to your `.bashrc`, `.zshrc`, or system environment:

```bash
echo 'export GITHUB_TOKEN="ghp_..."' >> ~/.bashrc
echo 'export SLACK_BOT_TOKEN="xoxb-..."' >> ~/.bashrc
# ... add all other tokens
source ~/.bashrc
```

---

## Running MCP Servers

### Individual Servers

Each MCP server can be run independently:

```bash
# GitHub MCP
cd mcp/github && python server.py

# Google MCP
cd mcp/google && python server.py

# Slack MCP
cd mcp/slack && python server.py

# Todoist MCP
cd mcp/todoist && python server.py

# Notion MCP
cd mcp/notion && python server.py

# Home Assistant MCP
cd mcp/homeassistant && python server.py

# HYD_AGENT_MCP
cd mcp/HYD_AGENT_MCP && python server.py
```

### Using Docker (if available)

If docker-compose configuration is available:

```bash
cd deployment
docker-compose up -d
```

---

## Security Best Practices

1. **Never commit credentials to git**
   - All credential files are in `.gitignore`
   - Always use `.example` files as templates

2. **Use environment variables**
   - Preferred method for credentials
   - Easy to manage across environments

3. **Restrict file permissions**
   ```bash
   chmod 600 mcp/google/credentials.json
   chmod 600 mcp/google/token.json
   chmod 600 deployment/.env
   ```

4. **Rotate credentials regularly**
   - Change tokens every 90 days
   - Revoke unused tokens immediately

5. **Use minimal permissions**
   - Only grant necessary scopes/permissions
   - Review API access regularly

---

## Troubleshooting

### Google OAuth Issues

If you get "redirect_uri_mismatch" error:
- Ensure redirect URI in Google Console matches `credentials.json`
- Default is `http://localhost`

### Environment Variables Not Loading

```bash
# Check if variables are set
echo $GITHUB_TOKEN

# If empty, reload .env
export $(cat deployment/.env | xargs)
```

### Permission Denied Errors

```bash
# Fix file permissions
chmod 600 mcp/google/*.json
chmod 600 deployment/.env
```

### Database Connection Issues (HYD_AGENT_MCP)

```bash
# Test PostgreSQL connection
psql -h localhost -U your_user -d mcp_memory

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

---

## Support

For detailed credential setup instructions, see:
- [CREDENTIALS-GUIDE.md](./CREDENTIALS-GUIDE.md) - Comprehensive guide for obtaining all credentials

For production deployment with n8n, Cloudflare Tunnel, and monitoring:
- Check `deployment/.env.example` for full production setup

---

## Quick Reference

| Service | Environment Variable | Required Scopes/Permissions |
|---------|---------------------|----------------------------|
| GitHub | `GITHUB_TOKEN` | repo, read:org, user |
| Google | `credentials.json` + `token.json` | Gmail, Drive, Calendar APIs |
| Slack | `SLACK_BOT_TOKEN` | channels:*, chat:write, users:read |
| Todoist | `TODOIST_API_TOKEN` | Full access |
| Notion | `NOTION_TOKEN` | Database access |
| Home Assistant | `HA_URL`, `HA_TOKEN` | Long-lived token |
| OpenAI | `OPENAI_API_KEY` | API access |
| OpenRouter | `OPENROUTER_API_KEY` | API access |

---

**Last Updated:** 2025-11-09
