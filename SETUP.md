# MCP Services - Complete Setup Guide

## Overview

This repository contains multiple MCP (Model Context Protocol) services running in Docker on Proxmox LXC Container 200.

## Available Services

- **Google MCP** ✅ - Gmail, Drive, Calendar (OAuth configured)
- **Outlook MCP** ⚙️ - Email, Calendar (Playwright, needs setup)
- **Todoist MCP** - Task management
- **Integrator MCP** - Cross-service orchestration
- **Hydraulic MCP** - AI schematic analysis

## Prerequisites

- Proxmox host with LXC container 200 (IP: 192.168.1.19)
- Docker and docker-compose installed in container
- Claude Desktop installed locally

## Quick Start

### 1. Clone Repository on Proxmox Host
```bash
cd /root/OBSIDIAN
git clone https://github.com/tchiro88/MCP_CREATOR.git
cd MCP_CREATOR
```

### 2. Configure Environment Variables
```bash
cd deployment
cp .env.example .env
nano .env
```

Add your credentials:
```bash
# Google OAuth (after OAuth setup)
GOOGLE_CREDENTIALS_FILE=/app/credentials/credentials.json
GOOGLE_TOKEN_FILE=/app/credentials/token.json

# Outlook
OUTLOOK_EMAIL=your.email@example.com
OUTLOOK_PASSWORD=your_password

# Add other service credentials as needed
```

### 3. Deploy to Container 200
```bash
# Copy to container
pct push 200 /root/OBSIDIAN/MCP_CREATOR /opt/MCP_CREATOR --recursive

# Build and start services
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml build'
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d'
```

## Service-Specific Setup

### Google MCP Setup

**Step 1: Generate OAuth URL**
```bash
cd /root/OBSIDIAN/MCP_CREATOR
python3 -m venv oauth_env
source oauth_env/bin/activate
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Create script to generate OAuth URL (see LEGACY/generate_token_port.py for reference)

**Step 2: Authorize in Browser**
- Open OAuth URL
- Sign in to Google
- Grant permissions
- Copy redirect URL

**Step 3: Exchange Code for Token**
Use the redirect URL to generate token.json

**Step 4: Deploy Token**
```bash
cp token.json deployment/credentials/google/
pct push 200 deployment/credentials/google/token.json /opt/MCP_CREATOR/deployment/credentials/google/token.json
```

**Step 5: Restart Service**
```bash
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml restart mcp-google'
```

### Outlook MCP Setup (Playwright)

**Step 1: Start Service**
```bash
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d mcp-outlook'
```

**Step 2: Initial Login (One-Time)**
```bash
pct exec 200 -- docker exec -it mcp-outlook python3 -c "
from outlook_web_client import OutlookWebClient
import asyncio
import os

async def login():
    email = os.getenv('OUTLOOK_EMAIL')
    password = os.getenv('OUTLOOK_PASSWORD')
    client = OutlookWebClient(email, password)
    await client.login(headless=True)
    print('Login complete!')

asyncio.run(login())
"
```

**Note:** If headless login fails due to 2FA, you may need to run with headless=False on a machine with display.

## Remote Access via Cloudflare Tunnel

To access your MCP services from any device (iPhone, laptop, etc.) without port forwarding:

### Quick Setup

**Step 1: Install cloudflared**
```bash
# In LXC Container 200
cd /tmp
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
cloudflared --version
```

**Step 2: Authenticate and Create Tunnel**
```bash
# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create autosapien-mcp
# Note the tunnel ID shown in output!
```

**Step 3: Configure DNS Routes**
```bash
cloudflared tunnel route dns autosapien-mcp google.autosapien.ai
cloudflared tunnel route dns autosapien-mcp outlook.autosapien.ai
cloudflared tunnel route dns autosapien-mcp todoist.autosapien.ai
cloudflared tunnel route dns autosapien-mcp icloud.autosapien.ai
cloudflared tunnel route dns autosapien-mcp integrator.autosapien.ai
cloudflared tunnel route dns autosapien-mcp hydraulic.autosapien.ai
```

**Step 4: Copy and Update Configuration**
```bash
# Copy configuration file
mkdir -p ~/.cloudflared
cp /opt/MCP_CREATOR/deployment/cloudflared-config.autosapien.yml ~/.cloudflared/config.yml

# Edit config and replace YOUR_TUNNEL_ID_HERE with your actual tunnel ID
nano ~/.cloudflared/config.yml

# Validate configuration
cloudflared tunnel ingress validate
```

**Step 5: Install and Start Service**
```bash
# Install as system service
sudo cloudflared service install

# Start and enable
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

**Step 6: Test Access**
```bash
# From any device with internet
curl -I https://google.autosapien.ai
curl -I https://outlook.autosapien.ai
curl -I https://integrator.autosapien.ai
```

### Detailed Guide

For complete step-by-step instructions with troubleshooting, see:
- **[CLOUDFLARE-TUNNEL-SETUP.md](CLOUDFLARE-TUNNEL-SETUP.md)** - Complete guide with verification steps

**Services exposed:**
- `google.autosapien.ai` - Google MCP (Gmail, Drive, Calendar)
- `outlook.autosapien.ai` - Outlook MCP (Email, Calendar)
- `todoist.autosapien.ai` - Todoist MCP (Tasks)
- `icloud.autosapien.ai` - iCloud MCP (Mail, Calendar, Contacts)
- `integrator.autosapien.ai` - Integrator MCP (Unified interface)
- `hydraulic.autosapien.ai` - Hydraulic MCP (Schematic analysis)

## Claude Desktop Configuration

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

### Option 1: Local Access (Docker Exec)

Use this if Claude Desktop is running on the same machine/network as your Docker containers:

```json
{
  "mcpServers": {
    "google": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-google", "python3", "/app/server.py"],
      "env": {}
    },
    "outlook": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-outlook", "python3", "/app/server.py"],
      "env": {}
    },
    "todoist": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-todoist", "python3", "/app/server.py"],
      "env": {}
    },
    "icloud": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-icloud", "python3", "/app/server.py"],
      "env": {}
    },
    "integrator": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-integrator", "python3", "/app/server.py"],
      "env": {}
    },
    "hydraulic": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-hydraulic", "python3", "/app/server.py"],
      "env": {}
    }
  }
}
```

**Note:** Requires Docker access from your local machine to container 200.

### Option 2: Remote Access (Cloudflare Tunnel) **Recommended**

Use this for access from any device (iPhone, laptop, desktop) anywhere:

```json
{
  "mcpServers": {
    "google": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://google.autosapien.ai"]
    },
    "outlook": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://outlook.autosapien.ai"]
    },
    "todoist": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://todoist.autosapien.ai"]
    },
    "icloud": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://icloud.autosapien.ai"]
    },
    "integrator": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://integrator.autosapien.ai"]
    },
    "hydraulic": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://hydraulic.autosapien.ai"]
    }
  }
}
```

**Benefits:**
- ✅ Works from any device with internet
- ✅ No VPN or SSH tunneling needed
- ✅ Secure via Cloudflare encryption
- ✅ DDoS protection included

**Prerequisites:** Complete [Cloudflare Tunnel Setup](#remote-access-via-cloudflare-tunnel) first.

## Troubleshooting

### Check Service Status
```bash
pct exec 200 -- docker ps --filter 'name=mcp-'
```

### View Logs
```bash
pct exec 200 -- docker logs -f mcp-google
pct exec 200 -- docker logs -f mcp-outlook
```

### Restart Service
```bash
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml restart mcp-google'
```

### Rebuild Service
```bash
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml build --no-cache mcp-google && docker compose -f docker-compose.autosapien.yml up -d mcp-google'
```

### Google OAuth Token Expired
Re-run OAuth flow to generate new token.json

### Outlook Session Expired
Re-run initial login process in container

### Service Shows "Restarting"
This is normal for stdio-based MCP servers. They wait for client connection and restart when stdin closes.

## Architecture

```
Claude Desktop (Local)
    ↓ (docker exec)
LXC Container 200 (192.168.1.19)
    ↓
Docker Containers
    ├─ mcp-google (Port 3004)
    ├─ mcp-outlook (Port 3010)
    ├─ mcp-todoist (Port 3005)
    ├─ mcp-integrator (Port 3011)
    └─ mcp-hydraulic (Port 3012)
```

## File Structure

```
MCP_CREATOR/
├── mcp/                      # MCP service implementations
│   ├── google/               # Google MCP (FastMCP + OAuth)
│   ├── outlook/              # Outlook MCP (Playwright)
│   ├── todoist/              # Todoist MCP
│   ├── integrator/           # Cross-service orchestrator
│   └── hydraulic/            # Hydraulic analysis
├── deployment/
│   ├── docker-compose.autosapien.yml
│   ├── credentials/          # Service credentials (gitignored)
│   └── .env                  # Environment variables
├── LEGACY/                   # Old files and scripts
├── SETUP.md                  # This file
├── SERVICES.md              # Quick reference
├── claude-desktop-config.json  # Claude Desktop config
└── CLAUDE-DESKTOP-SETUP.md  # Detailed Claude Desktop guide
```

## Security Notes

- Credentials are in `deployment/credentials/` (gitignored)
- OAuth tokens should be rotated periodically
- Session files contain authentication state
- Never commit credentials to git

## Support & Documentation

- Main documentation: README.md
- Claude Desktop guide: CLAUDE-DESKTOP-SETUP.md
- Services reference: SERVICES.md
- Legacy files: LEGACY/ folder

## Next Steps

1. ✅ Configure Google OAuth (if not done)
2. ✅ Set up Outlook Playwright login
3. ✅ Configure other services as needed
4. ✅ Set up Cloudflare Tunnel for remote access (see [CLOUDFLARE-TUNNEL-SETUP.md](CLOUDFLARE-TUNNEL-SETUP.md))
5. ✅ Add to Claude Desktop (use Option 2 for remote access)
6. ✅ Test each service

For detailed service-specific information, see each service's README in `mcp/[service]/README.md`
