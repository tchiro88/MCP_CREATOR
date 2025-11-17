# Minimal MCP Setup - Quick Start Guide

**Goal**: Get basic MCP connectors running that you can access from any device (iPhone, laptop, etc.) with minimal complexity.

> 📖 **For complete deployment on Proxmox with all 7 connectors**, see [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)

## What You Get

- ✅ **GitHub MCP** - Git operations, repo management
- ✅ **Google MCP** - Gmail, Drive, Calendar
- ✅ **Todoist MCP** - Task management
- ✅ **Remote access** - Works from iPhone, laptop, anywhere
- ✅ **Secure** - No port forwarding needed with Cloudflare Tunnel
- ❌ **NO n8n** - Too complex for basic needs
- ❌ **NO databases** - Not needed
- ❌ **NO extra services** - Just the essentials

## Prerequisites

1. A domain name (or subdomain) pointed to Cloudflare
2. A server to run Docker (home server, VPS, Proxmox LXC, etc.)
3. Credentials for services you want to connect (see [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md))

## Setup (15 minutes)

### Step 1: Install Cloudflare Tunnel

```bash
# On your server
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create mcp-tunnel

# Save the tunnel ID that's displayed!
```

### Step 2: Setup DNS

```bash
# Route your domains to the tunnel
cloudflared tunnel route dns mcp-tunnel github.yourdomain.com
cloudflared tunnel route dns mcp-tunnel files.yourdomain.com

# Add more as needed:
# cloudflared tunnel route dns mcp-tunnel gmail.yourdomain.com
# cloudflared tunnel route dns mcp-tunnel drive.yourdomain.com
```

### Step 3: Get Tunnel Token

```bash
# Get your tunnel token
cloudflared tunnel token mcp-tunnel

# Copy the token - you'll need it next
```

### Step 4: Configure Environment

```bash
cd MCP_CREATOR/deployment

# Copy example env file
cp .env.minimal.example .env

# Edit with your values
nano .env
```

Add your credentials (see [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md) for how to obtain these):
```bash
CLOUDFLARE_TUNNEL_TOKEN=eyJh...your-tunnel-token
GITHUB_TOKEN=ghp_your-github-token
TODOIST_API_TOKEN=your-todoist-token
# Add others as needed
```

**For Google services**, you'll also need OAuth credentials:
```bash
# See CREDENTIALS-GUIDE.md for detailed instructions
# You need: credentials.json and token.json in deployment/credentials/google/
```

**📋 Copying credentials from your laptop to server?** See [Step 3 in DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md#step-3-copy-credentials-from-laptop-to-proxmox)

### Step 5: Start Services

```bash
# Start with minimal setup
docker-compose -f docker-compose.minimal.yml up -d

# Check logs
docker-compose -f docker-compose.minimal.yml logs -f
```

### Step 6: Test Access

```bash
# Test from anywhere
curl https://github.yourdomain.com/health
curl https://files.yourdomain.com/health
```

## Configure Claude Apps

### Claude Desktop (Laptop)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github": {
      "url": "https://github.yourdomain.com",
      "transport": "http"
    },
    "files": {
      "url": "https://files.yourdomain.com",
      "transport": "http"
    }
  }
}
```

### Claude iPhone App

1. Open Claude app
2. Go to Settings → Integrations
3. Add MCP Server:
   - Name: GitHub
   - URL: `https://github.yourdomain.com`
4. Repeat for filesystem:
   - Name: Files
   - URL: `https://files.yourdomain.com`

### Claude Code (Any Machine)

Edit: `~/.config/claude-code/config.json`

```json
{
  "mcpServers": {
    "github": {
      "url": "https://github.yourdomain.com",
      "transport": "http"
    },
    "files": {
      "url": "https://files.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Google Services (Gmail, Drive, Calendar)

**Good news!** This repository includes a complete Google MCP connector.

**Setup requires OAuth authentication** (one-time setup on your laptop):

```bash
# On your laptop
cd mcp/google
pip install -r requirements.txt

# Copy your Google OAuth credentials.json here
# (See CREDENTIALS-GUIDE.md for how to get this)

# Authenticate (opens browser)
python server.py

# This creates token.json
# Copy both files to your server
```

**See detailed instructions**: [CREDENTIALS-GUIDE.md - Google Services](CREDENTIALS-GUIDE.md#google-services-gmail-drive-calendar)

## Security (Optional but Recommended)

Add Cloudflare Zero Trust authentication:

1. Go to: https://one.dash.cloudflare.com/
2. Access → Applications → Add application
3. Select: Self-hosted
4. Domain: `*.yourdomain.com`
5. Add policy: "Allow emails: your-email@gmail.com"

Now only you can access your MCP servers!

## Troubleshooting

**Tunnel not connecting?**
```bash
# Check tunnel status
docker-compose -f docker-compose.minimal.yml logs cloudflared

# Test locally first
curl http://localhost:3001/health
```

**502 Bad Gateway?**
- MCP server might not be running
- Check: `docker-compose ps`

**Can't access from iPhone?**
- Verify DNS: `nslookup github.yourdomain.com`
- Check Cloudflare dashboard for SSL/TLS mode (should be "Full")

## Next Steps

Once this is working, you can:
1. **Add more connectors** - This repository includes 7 ready-to-use connectors
2. **Add Zero Trust authentication** - Secure your endpoints (see DEPLOYMENT-GUIDE.md)
3. **Deploy on Proxmox** - See [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) for complete Proxmox LXC setup
4. **Build custom MCP servers** - Use `examples/simple-mcp-server/` as a template

## Available Connectors in This Repository

| Connector | What It Does | Documentation |
|-----------|--------------|---------------|
| GitHub | Repos, issues, PRs | [mcp/github/README.md](mcp/github/README.md) |
| Google | Gmail, Drive, Calendar, Photos | [mcp/google/README.md](mcp/google/README.md) |
| Todoist | Task management | [mcp/todoist/README.md](mcp/todoist/README.md) |
| Home Assistant | Smart home control | [mcp/homeassistant/README.md](mcp/homeassistant/README.md) |
| Notion | Databases, pages | [mcp/notion/README.md](mcp/notion/README.md) |
| Slack | Messages, channels | [mcp/slack/README.md](mcp/slack/README.md) |
| iCloud | Mail, calendar, contacts | [mcp/icloud/README.md](mcp/icloud/README.md) |

## Cost

- **Cloudflare Tunnel**: Free
- **Server**: $0 (home server/Proxmox) or $5-10/month (VPS)
- **Domain**: $10-15/year

Total: **~$10-15/year** (just the domain if using home server)

---

## More Resources

- 📖 **Complete Deployment**: [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) - Full Proxmox deployment with all connectors
- 🔑 **Get Credentials**: [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md) - How to obtain all API keys and tokens
- 📋 **Individual Connectors**: See `mcp/*/README.md` for each connector

**That's it!** No n8n, no complexity, just simple remote MCP access.
