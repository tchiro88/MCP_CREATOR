# Minimal MCP Setup - Quick Start Guide

**Goal**: Get basic MCP connectors running that you can access from any device (iPhone, laptop, etc.) with minimal complexity.

## What You Get

- ✅ **GitHub MCP** - Git operations, repo management
- ✅ **Filesystem MCP** - File access
- ✅ **Remote access** - Works from iPhone, laptop, anywhere
- ✅ **Secure** - No port forwarding needed
- ❌ **NO n8n** - Too complex for basic needs
- ❌ **NO databases** - Not needed
- ❌ **NO extra services** - Just the essentials

## Prerequisites

1. A domain name (or subdomain) pointed to Cloudflare
2. A server to run Docker (home server, VPS, etc.)
3. GitHub account (for GitHub MCP)

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
cd MCP-connectors/deployment

# Copy example env file
cp .env.minimal.example .env

# Edit with your values
nano .env
```

Add:
```bash
CLOUDFLARE_TUNNEL_TOKEN=eyJh...your-token-here
GITHUB_TOKEN=ghp_your-github-token
```

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

## What About Gmail and Google Drive?

**Problem**: There aren't many ready-made MCP servers for these yet.

**Options**:

### Option 1: Wait for Community Servers
Check these regularly:
- https://github.com/topics/mcp-server
- https://www.npmjs.com/search?q=mcp%20server

### Option 2: Use Google Apps Script + Webhook MCP
Create Google Apps Script that exposes Gmail/Drive via webhooks, then create simple MCP server that calls those webhooks.

### Option 3: Build Your Own (Simple!)
Use the example in `examples/simple-mcp-server/` as a template:

```javascript
// Simple Gmail MCP server skeleton
server.setRequestHandler('tools/list', async () => ({
  tools: [{
    name: 'search_gmail',
    description: 'Search Gmail messages',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' }
      }
    }
  }]
}));

server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'search_gmail') {
    // Use Gmail API here
    const results = await searchGmail(request.params.arguments.query);
    return { content: [{ type: 'text', text: JSON.stringify(results) }] };
  }
});
```

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
1. Add more MCP servers as they become available
2. Build custom MCP servers for your specific needs
3. Add Zero Trust authentication
4. Set up monitoring

## Cost

- **Cloudflare Tunnel**: Free
- **Server**: $0 (home server) or $5-10/month (VPS)
- **Domain**: $10-15/year

Total: **~$10-15/year** (just the domain if using home server)

---

**That's it!** No n8n, no complexity, just simple remote MCP access.
