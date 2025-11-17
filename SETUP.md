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

## Claude Desktop Configuration

Copy this configuration to your Claude Desktop settings:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

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

1. Configure Google OAuth (if not done)
2. Set up Outlook Playwright login
3. Configure other services as needed
4. Add to Claude Desktop
5. Test each service

For detailed service-specific information, see each service's README in `mcp/[service]/README.md`
