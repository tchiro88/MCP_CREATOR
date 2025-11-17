# Claude Desktop MCP Setup Guide

This guide explains how to connect Claude Desktop to your deployed MCP services.

## Overview

Your MCP services are running in Docker containers on LXC Container 200 (IP: 192.168.1.19) and are accessible via Cloudflare tunnels.

## Available Services

| Service | Port | Cloudflare URL | Description |
|---------|------|----------------|-------------|
| Google | 3004 | google.autosapien.ai | Gmail, Drive, Calendar |
| iCloud | 3009 | icloud.autosapien.ai | Mail, Calendar, Contacts |
| Outlook | 3010 | outlook.autosapien.ai | Email, Calendar |
| Todoist | 3005 | todoist.autosapien.ai | Task Management |
| Integrator | 3011 | integrator.autosapien.ai | Cross-service orchestration |
| Hydraulic | 3012 | hydraulic.autosapien.ai | AI schematic analysis |

## Claude Desktop Configuration

### Option 1: Via Cloudflare Tunnel (Recommended for External Access)

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "google": {
      "url": "https://google.autosapien.ai"
    },
    "icloud": {
      "url": "https://icloud.autosapien.ai"
    },
    "outlook": {
      "url": "https://outlook.autosapien.ai"
    },
    "todoist": {
      "url": "https://todoist.autosapien.ai"
    },
    "integrator": {
      "url": "https://integrator.autosapien.ai"
    },
    "hydraulic": {
      "url": "https://hydraulic.autosapien.ai"
    }
  }
}
```

### Option 2: Direct Connection (Local Network Only)

If you're on the same network as the server:

```json
{
  "mcpServers": {
    "google": {
      "url": "http://192.168.1.19:3004"
    },
    "icloud": {
      "url": "http://192.168.1.19:3009"
    },
    "outlook": {
      "url": "http://192.168.1.19:3010"
    },
    "todoist": {
      "url": "http://192.168.1.19:3005"
    },
    "integrator": {
      "url": "http://192.168.1.19:3011"
    },
    "hydraulic": {
      "url": "http://192.168.1.19:3012"
    }
  }
}
```

### Option 3: SSH Tunnel (Most Secure)

If you want to tunnel through SSH:

```bash
# Set up SSH tunnel
ssh -L 3004:192.168.1.19:3004 \
    -L 3009:192.168.1.19:3009 \
    -L 3010:192.168.1.19:3010 \
    -L 3005:192.168.1.19:3005 \
    -L 3011:192.168.1.19:3011 \
    -L 3012:192.168.1.19:3012 \
    root@192.168.1.32
```

Then configure Claude Desktop to use localhost:

```json
{
  "mcpServers": {
    "google": {
      "url": "http://localhost:3004"
    },
    "icloud": {
      "url": "http://localhost:3009"
    },
    "outlook": {
      "url": "http://localhost:3010"
    },
    "todoist": {
      "url": "http://localhost:3005"
    },
    "integrator": {
      "url": "http://localhost:3011"
    },
    "hydraulic": {
      "url": "http://localhost:3012"
    }
  }
}
```

## Service-Specific Setup

### Google MCP Service

**Prerequisites:**
- Google OAuth credentials configured
- OAuth token generated (see [Google OAuth Setup](#google-oauth-setup))

**Available Tools:**
- `gmail_search_messages` - Search Gmail
- `gmail_send_email` - Send emails
- `drive_list` - List Drive files
- `drive_search` - Search Drive
- `drive_get_file` - Get file details
- `calendar_list` - List calendar events
- `calendar_create` - Create calendar events
- `photos_list` - List photos albums
- `photos_search_items` - Search photos
- `photos_get_item` - Get photo details

**Resources:**
- `gmail://inbox` - Gmail inbox messages
- `drive://files` - Google Drive files
- `calendar://events` - Calendar events
- `photos://albums` - Photo albums
- `photos://recent` - Recent photos

### iCloud MCP Service

**Prerequisites:**
- iCloud account with app-specific password
- App-specific password configured in credentials

**Available Tools:**
- Mail management
- Calendar access
- Contacts management

### Other Services

Each service provides domain-specific tools and resources. Refer to the service's documentation for details.

## Troubleshooting

### Connection Issues

**Check service status:**
```bash
# SSH to Proxmox host
ssh root@192.168.1.32

# Check container status
pct exec 200 -- docker ps

# View service logs
pct exec 200 -- docker logs mcp-google -f
pct exec 200 -- docker logs mcp-icloud -f
```

**Common issues:**

1. **"Cannot connect to server"**
   - Verify the service is running: `docker ps`
   - Check port mappings: `docker port mcp-google`
   - Verify firewall rules allow the port

2. **"Authentication failed"**
   - Check OAuth token is valid (Google)
   - Verify app-specific password (iCloud)
   - Review service logs for auth errors

3. **"Service restarting continuously"**
   - This is normal for stdio-based MCP servers without active clients
   - The service will stabilize once Claude Desktop connects
   - Check logs for actual errors vs. normal restarts

## Google OAuth Setup

The Google MCP service requires OAuth authentication. Follow these steps:

### 1. Generate OAuth URL

```bash
cd /root/OBSIDIAN/MCP_CREATOR
oauth_venv/bin/python generate_token_port.py 8080
```

### 2. Authorize in Browser

- Copy the OAuth URL from the output
- Open it in your browser
- Sign in to your Google account
- Authorize the requested permissions
- Copy the redirect URL from your browser (even if the page doesn't load)

### 3. Complete Token Generation

```bash
oauth_venv/bin/python exchange_code.py 'PASTE_REDIRECT_URL_HERE'
```

### 4. Deploy Token

The token is automatically saved to `deployment/credentials/google/token.json` and will be used by the service.

### 5. Restart Service

```bash
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml restart mcp-google'
```

## Monitoring

### View All Service Logs

```bash
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml logs -f'
```

### View Specific Service

```bash
pct exec 200 -- docker logs mcp-google -f
```

### Check Service Status

```bash
pct exec 200 -- docker ps --filter 'name=mcp-'
```

## Security Notes

- **Credentials:** Never commit credentials to git (see `.gitignore`)
- **Cloudflare Tunnel:** Provides encrypted access without exposing ports
- **SSH Tunnel:** Most secure option for direct access
- **Network Access:** Direct IP access only works on local network

## Support

For issues or questions:
1. Check service logs first
2. Review this documentation
3. Check the main README.md for deployment details
4. Review individual service documentation in `mcp/[service]/README.md`

## Architecture Notes

### Why Services Show "Restarting"

MCP servers using stdio architecture (standard input/output) will show as "Restarting" in Docker when no client is connected. This is expected behavior:

1. Service starts successfully
2. Waits for stdio input from client
3. Docker closes stdin (no client connected)
4. Service exits cleanly (exit code 0)
5. Docker restarts it automatically
6. Cycle repeats until client connects

**This is normal and indicates the service is working correctly.**

### Service Architecture

- **Transport:** HTTP (FastMCP) for most services
- **Port Mapping:** Internal port 3000 → External ports 3004-3012
- **Network:** Services run in Docker network on LXC container
- **Access:** Via Cloudflare tunnel or direct IP

## Next Steps

1. Choose your connection method (Cloudflare, Direct, or SSH tunnel)
2. Update your Claude Desktop configuration
3. Restart Claude Desktop
4. Verify services appear in Claude Desktop's MCP section
5. Test functionality by asking Claude to use the services
