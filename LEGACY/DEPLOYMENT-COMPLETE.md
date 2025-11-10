# MCP Infrastructure - Complete Deployment Guide

**Status**: ✅ Production Ready - All 6 Connectors Built

This guide provides complete deployment instructions for your MCP (Model Context Protocol) infrastructure with remote access from any device.

## 🎯 What You're Deploying

A complete MCP server infrastructure accessible from:
- 📱 iPhone (Claude app)
- 💻 Laptop (Claude Desktop, Claude Code)
- 🌐 Any device with internet access

## 📦 Included MCP Connectors

| Connector | Port | Services | Status |
|-----------|------|----------|--------|
| **GitHub** | 3001 | Repositories, Issues, PRs | ✅ Built |
| **Google** | 3004 | Gmail, Drive, Calendar, Photos | ✅ Built |
| **Todoist** | 3005 | Tasks, Projects, Comments | ✅ Built |
| **Home Assistant** | 3006 | Smart Home Control | ✅ Built |
| **Notion** | 3007 | Databases, Pages, Workspaces | ✅ Built |
| **Slack** | 3008 | Messages, Channels, Files | ✅ Built |

## 🏗️ Architecture

```
┌─────────────────┐
│  Your Devices   │
│ iPhone, Laptop  │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│ Cloudflare      │
│ Tunnel + ZT     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│     Proxmox LXC Container       │
│  ┌───────────────────────────┐  │
│  │  Docker Compose Network   │  │
│  │                           │  │
│  │  ┌─────┐  ┌─────┐        │  │
│  │  │ MCP │  │ MCP │  ...   │  │
│  │  │  #1 │  │  #2 │        │  │
│  │  └─────┘  └─────┘        │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

## 🚀 Quick Start Deployment

### Prerequisites

- ✅ Proxmox server
- ✅ Cloudflare account with domain
- ✅ Basic Linux/Docker knowledge

### Step 1: Create Proxmox LXC

```bash
# On Proxmox host
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname mcp-server \
  --memory 4096 \
  --swap 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --storage local-lvm \
  --rootfs local-lvm:32 \
  --unprivileged 1 \
  --features nesting=1

# Start container
pct start 200

# Enter container
pct enter 200
```

### Step 2: Install Docker in LXC

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
apt install -y curl
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install -y docker-compose

# Verify
docker --version
docker-compose --version
```

### Step 3: Clone Repository

```bash
# Install git
apt install -y git

# Clone repo
cd /opt
git clone https://github.com/yourusername/MCP_CREATOR.git
cd MCP_CREATOR
```

### Step 4: Configure Credentials

#### Create `.env` file

```bash
cd deployment
cp .env.minimal.example .env
nano .env
```

Fill in your credentials:

```bash
# Cloudflare Tunnel Token
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token

# GitHub Token (https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Todoist API Token (https://todoist.com/prefs/integrations)
TODOIST_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Home Assistant
HA_URL=http://homeassistant.local:8123
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Notion Integration Token (https://www.notion.so/my-integrations)
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Slack Bot Token (https://api.slack.com/apps)
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

#### Setup Google OAuth

Google requires OAuth flow:

```bash
# Create credentials directory
mkdir -p credentials/google

# On your LOCAL machine (not server):
# 1. Run the Google MCP server locally (see mcp/google/README.md)
# 2. Complete OAuth flow in browser
# 3. This generates token.json

# Copy credentials to server
scp mcp/google/credentials.json root@your-lxc-ip:/opt/MCP_CREATOR/deployment/credentials/google/
scp mcp/google/token.json root@your-lxc-ip:/opt/MCP_CREATOR/deployment/credentials/google/
```

### Step 5: Setup Cloudflare Tunnel

#### Create Tunnel

```bash
# On your local machine with cloudflared installed
cloudflared tunnel login
cloudflared tunnel create mcp-tunnel

# Copy tunnel ID and token to .env file
```

#### Configure DNS

```bash
# Add DNS records in Cloudflare dashboard for each MCP:
# github.yourdomain.com → mcp-tunnel
# google.yourdomain.com → mcp-tunnel
# todoist.yourdomain.com → mcp-tunnel
# homeassistant.yourdomain.com → mcp-tunnel
# notion.yourdomain.com → mcp-tunnel
# slack.yourdomain.com → mcp-tunnel
```

Or use CLI:

```bash
cloudflared tunnel route dns mcp-tunnel github.yourdomain.com
cloudflared tunnel route dns mcp-tunnel google.yourdomain.com
cloudflared tunnel route dns mcp-tunnel todoist.yourdomain.com
cloudflared tunnel route dns mcp-tunnel homeassistant.yourdomain.com
cloudflared tunnel route dns mcp-tunnel notion.yourdomain.com
cloudflared tunnel route dns mcp-tunnel slack.yourdomain.com
```

### Step 6: Deploy Stack

```bash
cd /opt/MCP_CREATOR/deployment

# Build and start all services
docker-compose -f docker-compose.minimal.yml up -d --build

# Check status
docker-compose -f docker-compose.minimal.yml ps

# View logs
docker-compose -f docker-compose.minimal.yml logs -f
```

Expected output:
```
NAME                  STATUS    PORTS
cloudflared           running
mcp-github            running   0.0.0.0:3001->3000/tcp
mcp-google            running   0.0.0.0:3004->3000/tcp
mcp-todoist           running   0.0.0.0:3005->3000/tcp
mcp-homeassistant     running   0.0.0.0:3006->3000/tcp
mcp-notion            running   0.0.0.0:3007->3000/tcp
mcp-slack             running   0.0.0.0:3008->3000/tcp
```

### Step 7: Configure Claude Apps

#### Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github": {
      "url": "https://github.yourdomain.com",
      "transport": "http"
    },
    "google": {
      "url": "https://google.yourdomain.com",
      "transport": "http"
    },
    "todoist": {
      "url": "https://todoist.yourdomain.com",
      "transport": "http"
    },
    "homeassistant": {
      "url": "https://homeassistant.yourdomain.com",
      "transport": "http"
    },
    "notion": {
      "url": "https://notion.yourdomain.com",
      "transport": "http"
    },
    "slack": {
      "url": "https://slack.yourdomain.com",
      "transport": "http"
    }
  }
}
```

Restart Claude Desktop.

#### Claude App (iPhone/iPad)

Same configuration works across devices!

## 🔧 Per-Connector Setup Guides

Detailed setup instructions for each connector:

### 1. GitHub
📖 See: [`mcp/github/README.md`](../mcp/github/README.md)

**Quick steps:**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Scopes: `repo`, `read:user`, `write:repo_hook`
4. Add to `.env` as `GITHUB_TOKEN`

### 2. Google Services
📖 See: [`mcp/google/README.md`](../mcp/google/README.md)

**Quick steps:**
1. Create project at https://console.cloud.google.com
2. Enable APIs: Gmail, Drive, Calendar, Photos Library
3. Create OAuth credentials
4. Run locally to authenticate
5. Copy `credentials.json` and `token.json` to server

### 3. Todoist
📖 See: [`mcp/todoist/README.md`](../mcp/todoist/README.md)

**Quick steps:**
1. Go to https://todoist.com/prefs/integrations
2. Scroll to API token
3. Copy token to `.env` as `TODOIST_API_TOKEN`

### 4. Home Assistant
📖 See: [`mcp/homeassistant/README.md`](../mcp/homeassistant/README.md)

**Quick steps:**
1. Log into Home Assistant
2. Profile → Long-Lived Access Tokens
3. Create token named "MCP Server"
4. Add to `.env` as `HA_TOKEN` and `HA_URL`

### 5. Notion
📖 See: [`mcp/notion/README.md`](../mcp/notion/README.md)

**Quick steps:**
1. Go to https://www.notion.so/my-integrations
2. Create new integration
3. Copy integration token
4. Share databases/pages with integration
5. Add to `.env` as `NOTION_TOKEN`

### 6. Slack
📖 See: [`mcp/slack/README.md`](../mcp/slack/README.md)

**Quick steps:**
1. Go to https://api.slack.com/apps
2. Create new app
3. Add bot token scopes (channels, chat, users, search, files)
4. Install to workspace
5. Copy bot token to `.env` as `SLACK_BOT_TOKEN`

## 📊 Port Reference

| Service | Internal | External (LXC) | Cloudflare Route |
|---------|----------|----------------|------------------|
| GitHub | 3000 | 3001 | github.yourdomain.com |
| Google | 3000 | 3004 | google.yourdomain.com |
| Todoist | 3000 | 3005 | todoist.yourdomain.com |
| Home Assistant | 3000 | 3006 | homeassistant.yourdomain.com |
| Notion | 3000 | 3007 | notion.yourdomain.com |
| Slack | 3000 | 3008 | slack.yourdomain.com |

## 🔐 Security Setup (Recommended)

### Add Cloudflare Zero Trust

Protect your MCP servers with authentication:

1. **Go to Cloudflare Zero Trust**
   - https://one.dash.cloudflare.com/

2. **Create Access Application**
   - Name: MCP Servers
   - Subdomain: `*.yourdomain.com`
   - Policy: Allow based on email

3. **Add Email Rule**
   - Allow: `your@email.com`

Now all MCP access requires login!

## 🧪 Testing

### Test Individual Connectors

```bash
# GitHub
curl https://github.yourdomain.com/health

# Google
curl https://google.yourdomain.com/health

# Todoist
curl https://todoist.yourdomain.com/health

# Home Assistant
curl https://homeassistant.yourdomain.com/health

# Notion
curl https://notion.yourdomain.com/health

# Slack
curl https://slack.yourdomain.com/health
```

### Test from Claude

Ask Claude:
> "List my GitHub repositories"
> "What emails do I have in Gmail?"
> "What tasks are due today in Todoist?"
> "Turn on the living room lights"
> "List my Notion databases"
> "Send a message to #general in Slack saying 'MCP is live!'"

## 🛠️ Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose.minimal.yml logs -f

# Specific service
docker-compose -f docker-compose.minimal.yml logs -f mcp-github

# Last 100 lines
docker-compose -f docker-compose.minimal.yml logs --tail=100
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.minimal.yml restart

# Restart specific
docker-compose -f docker-compose.minimal.yml restart mcp-github

# Rebuild and restart
docker-compose -f docker-compose.minimal.yml up -d --build mcp-github
```

### Update Connectors

```bash
cd /opt/MCP_CREATOR
git pull
cd deployment
docker-compose -f docker-compose.minimal.yml up -d --build
```

### Backup Credentials

```bash
# Backup .env and credentials
tar -czf mcp-backup-$(date +%Y%m%d).tar.gz \
  .env \
  credentials/

# Store safely!
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.minimal.yml logs mcp-github

# Common issues:
# - Missing environment variable
# - Invalid credentials
# - Port already in use
```

### Can't Access via Cloudflare

```bash
# Check tunnel status
docker-compose -f docker-compose.minimal.yml logs cloudflared

# Verify DNS records
nslookup github.yourdomain.com

# Check tunnel config
cat cloudflared-minimal.example.yml
```

### Google OAuth Issues

```bash
# Re-authenticate locally
cd /opt/MCP_CREATOR/mcp/google
python3 server.py

# Copy new token.json to server
scp token.json root@lxc-ip:/opt/MCP_CREATOR/deployment/credentials/google/

# Restart container
docker-compose -f docker-compose.minimal.yml restart mcp-google
```

### Home Assistant Connection Failed

```bash
# Test HA from LXC
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://homeassistant.local:8123/api/

# Check if HA is accessible from LXC network
ping homeassistant.local

# May need to use IP instead of hostname
HA_URL=http://192.168.1.100:8123
```

## 📈 Scaling

### Add More MCP Connectors

1. Create new connector in `/mcp/yourservice/`
2. Add to `docker-compose.minimal.yml`
3. Add route to `cloudflared-minimal.example.yml`
4. Add credentials to `.env`
5. Rebuild: `docker-compose up -d --build`

### Separate LXCs per Connector

For resource isolation:

```bash
# Create separate LXC for each heavy connector
# Example: Separate LXC for Google MCP
pct create 201 ... --hostname mcp-google
```

## 🎉 You're Done!

Your complete MCP infrastructure is now deployed and accessible from any device!

### What You Can Do Now

✅ Access all 6 services from iPhone/laptop/any device
✅ Use Claude to manage GitHub, Gmail, Tasks, Home, Notion, Slack
✅ Secure remote access via Cloudflare
✅ Easy to maintain and update

### Next Steps

- Set up Cloudflare Zero Trust for authentication
- Create backup automation
- Monitor logs for issues
- Add more MCP connectors as needed

### Support

Each connector has detailed documentation:
- 📖 `/mcp/github/README.md`
- 📖 `/mcp/google/README.md`
- 📖 `/mcp/todoist/README.md`
- 📖 `/mcp/homeassistant/README.md`
- 📖 `/mcp/notion/README.md`
- 📖 `/mcp/slack/README.md`

---

**Built with**: Docker, Cloudflare Tunnel, MCP SDK, Python 3.11

**Deployed on**: Proxmox LXC

**Accessible from**: Anywhere 🌍
