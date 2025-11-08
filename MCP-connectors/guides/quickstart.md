# MCP Connectors - Quick Start Guide

Get your self-hosted MCP infrastructure up and running in under 30 minutes!

## What You'll Build

By the end of this guide, you'll have:

- ✅ n8n workflow automation platform running locally
- ✅ n8n-MCP server for AI-powered workflow creation
- ✅ Cloudflare Tunnel exposing your MCP servers securely
- ✅ Claude Desktop connected to your self-hosted MCP infrastructure

## Prerequisites

### Required

- [x] **Computer** with Linux, macOS, or Windows (with WSL2)
- [x] **Docker** and Docker Compose installed
- [x] **Cloudflare Account** (free tier is fine)
- [x] **Domain Name** added to Cloudflare
- [x] **Basic terminal knowledge**

### Optional

- [ ] Claude Desktop app
- [ ] Node.js 18+ (if not using Docker)

## Step 1: Clone This Repository

```bash
cd ~/
git clone <this-repo-url>
cd Personal_GIT/MCP-connectors
```

## Step 2: Set Up Environment Variables

```bash
# Copy example environment file
cp deployment/.env.example deployment/.env

# Edit with your values
nano deployment/.env
```

**Minimum required variables**:

```bash
# n8n credentials
N8N_USER=admin
N8N_PASSWORD=your-secure-password

# Generate n8n API key after starting n8n (step 4)
N8N_API_KEY=your-api-key-here

# Your domain
N8N_WEBHOOK_URL=https://n8n.yourdomain.com

# Cloudflare Tunnel (get in step 3)
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
```

## Step 3: Set Up Cloudflare Tunnel

### 3.1 Install cloudflared

**macOS**:
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Linux (Debian/Ubuntu)**:
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

**Linux (RHEL/CentOS)**:
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
sudo rpm -i cloudflared-linux-x86_64.rpm
```

### 3.2 Authenticate

```bash
cloudflared tunnel login
```

This opens a browser to select your domain. Choose the domain you'll use for MCP.

### 3.3 Create Tunnel

```bash
cloudflared tunnel create mcp-tunnel
```

**Output**:
```
Created tunnel mcp-tunnel with id: abc123-def456-ghi789
Credentials file: ~/.cloudflared/abc123-def456-ghi789.json
```

**Save this tunnel ID!**

### 3.4 Get Tunnel Token (for Docker)

```bash
cloudflared tunnel token mcp-tunnel
```

Copy the token (starts with `eyJ...`) and add it to `deployment/.env`:

```bash
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiNjk...
```

### 3.5 Route DNS

```bash
# Route your domains to the tunnel
cloudflared tunnel route dns mcp-tunnel mcp-n8n.yourdomain.com
cloudflared tunnel route dns mcp-tunnel n8n.yourdomain.com
```

## Step 4: Start the Stack

```bash
cd deployment
docker-compose up -d
```

This starts:
- **n8n** (http://localhost:5678)
- **n8n-mcp** (http://localhost:3003)
- **cloudflared** (tunnel to Cloudflare)
- **redis** (caching)
- **postgres** (database)

Check status:
```bash
docker-compose ps
```

All services should show "Up" status.

## Step 5: Configure n8n

### 5.1 Access n8n

Open: http://localhost:5678 (or https://n8n.yourdomain.com if tunnel is running)

### 5.2 Complete Setup

- Create admin account (use credentials from `.env`)
- Skip email verification (for self-hosted)

### 5.3 Generate API Key

1. Click your profile (bottom left)
2. Go to: **Settings → API**
3. Click: **Create API Key**
4. Copy the key

### 5.4 Update Environment

Add the API key to `deployment/.env`:

```bash
N8N_API_KEY=n8n_api_abc123...
```

Restart n8n-mcp:
```bash
docker-compose restart n8n-mcp
```

## Step 6: Verify MCP Server

### 6.1 Check Health

```bash
# n8n-MCP health check
curl http://localhost:3003/health

# Expected output:
# {"status":"ok","uptime":123,"timestamp":"..."}
```

### 6.2 Test via Cloudflare Tunnel

```bash
curl https://mcp-n8n.yourdomain.com/health
```

If this works, your MCP server is publicly accessible!

## Step 7: Configure Claude Desktop

### 7.1 Find Config File

**macOS**:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux**:
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### 7.2 Add MCP Server

**For local testing (stdio mode)**:

```json
{
  "mcpServers": {
    "n8n-local": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "your-n8n-api-key",
        "MCP_MODE": "stdio"
      }
    }
  }
}
```

**For remote access (HTTP mode)**:

```json
{
  "mcpServers": {
    "n8n-remote": {
      "url": "https://mcp-n8n.yourdomain.com",
      "transport": "http"
    }
  }
}
```

### 7.3 Restart Claude Desktop

Completely quit and restart Claude Desktop for changes to take effect.

## Step 8: Test It!

### 8.1 Open Claude Desktop

### 8.2 Test Connection

Ask Claude:

```
Can you list all n8n nodes available?
```

Claude should respond with a list of n8n nodes, proving the MCP connection works!

### 8.3 Create a Workflow

```
Create an n8n workflow that sends me a Slack message every morning at 9am saying "Good morning!"
```

Claude will create the workflow via the MCP server!

## What's Next?

### Add More MCP Servers

1. Edit `deployment/docker-compose.yml`
2. Uncomment example servers (GitHub, Database)
3. Add credentials to `.env`
4. Add routes to Cloudflare Tunnel config
5. Restart: `docker-compose up -d`

### Add Authentication (Zero Trust)

1. Go to Cloudflare Zero Trust dashboard
2. Create Application for your MCP servers
3. Add access policies (email, 2FA, etc.)
4. Your MCP servers are now secured!

### Create Custom MCP Server

1. Copy `examples/simple-mcp-server`
2. Customize tools, resources, prompts
3. Add to `docker-compose.yml`
4. Expose via Cloudflare Tunnel

## Troubleshooting

### n8n-MCP can't connect to n8n

**Check**:
```bash
# Is n8n running?
curl http://localhost:5678/healthz

# Can n8n-mcp reach it?
docker-compose exec n8n-mcp wget -q -O- http://n8n:5678/healthz
```

**Fix**: Ensure `N8N_API_URL` in `.env` points to `http://n8n:5678` (not localhost)

### Cloudflare Tunnel not working

**Check logs**:
```bash
docker-compose logs cloudflared
```

**Common issues**:
- Wrong tunnel token
- DNS not propagated (wait 5-10 minutes)
- Firewall blocking outbound HTTPS

### Claude Desktop can't find MCP server

**Check**:
1. Config file syntax (must be valid JSON)
2. Paths are absolute (not relative)
3. Restart Claude Desktop completely
4. Check Claude Desktop logs

**macOS logs**:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

### "Rate limit exceeded" errors

**Cause**: Too many requests to MCP server

**Fix**: Implement caching or increase rate limits in your MCP server

## Architecture Overview

Here's what you just built:

```
┌─────────────┐
│   Claude    │ (Your desktop)
│  Desktop    │
└──────┬──────┘
       │
       │ (Local: stdio)
       │ (Remote: HTTPS via Cloudflare)
       │
       ▼
┌──────────────────┐
│  Cloudflare      │
│  Tunnel          │
└──────┬───────────┘
       │ (Encrypted tunnel)
       │
       ▼
┌──────────────────┐
│  Your Home       │
│  Network         │
│                  │
│  ┌────────────┐  │
│  │ n8n-MCP    │  │
│  └─────┬──────┘  │
│        │         │
│  ┌─────▼──────┐  │
│  │    n8n     │  │
│  └────────────┘  │
└──────────────────┘
```

## Security Checklist

- [ ] Changed default n8n password
- [ ] Generated strong n8n API key
- [ ] Using Cloudflare Tunnel (not port forwarding)
- [ ] Environment variables in `.env` (not committed to Git)
- [ ] Cloudflare Zero Trust configured (optional but recommended)
- [ ] Regular backups of n8n workflows
- [ ] HTTPS only (via Cloudflare)

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Cloudflare Tunnel | Free |
| Cloudflare Zero Trust | Free (up to 50 users) |
| Domain | $10-15/year |
| Self-hosted server | $0 (your hardware) |
| **Total** | **$10-15/year** |

Compare to Zapier: $29.99/month ($360/year)!

## Support

If you run into issues:

1. Check this guide's troubleshooting section
2. Review the architecture docs in `/architecture`
3. Check example configurations in `/examples`
4. Review Cloudflare Tunnel logs: `docker-compose logs cloudflared`

## Next Steps

- [ ] Read [Architecture Guide](../architecture/self-hosted-architecture.md)
- [ ] Set up [OAuth 2.1 Authentication](../research/security-oauth.md)
- [ ] Explore [n8n Integration Patterns](../architecture/n8n-integration.md)
- [ ] Deploy [Custom MCP Servers](../examples/)
- [ ] Configure [Monitoring & Alerts](production-deployment.md)

---

**Congratulations!** 🎉

You now have a self-hosted MCP infrastructure that rivals Zapier and other integration platforms, with full control over your data and infrastructure!

**Document Version**: 1.0
**Last Updated**: November 8, 2025
