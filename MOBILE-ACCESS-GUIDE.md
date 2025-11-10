# Accessing MCP Services from Claude

## ⚠️ Important: Claude Mobile App Limitation

**The Claude mobile app does NOT support MCP servers directly.**

MCP (Model Context Protocol) is currently only supported in:
- ✅ Claude Desktop App (Mac/Windows)
- ✅ Custom MCP clients
- ✅ API integrations

## Current Deployment Status

```
WORKING NOW:
✅ mcp-google (Port 3004)
✅ mcp-hydraulic (Port 3012)

NEEDS CREDENTIALS:
❌ mcp-icloud - Need app-specific password
❌ mcp-todoist - Need token verification
❌ mcp-outlook - Need credential verification
❌ mcp-integrator - Deploy after others work
```

## Option A: Use Claude Desktop App (Recommended)

### Requirements
- Claude Desktop App installed (https://claude.ai/download)
- SSH tunnel to container 200
- MCP server configuration

### Setup Steps

#### 1. Install Claude Desktop App
Download from: https://claude.ai/download

#### 2. Configure MCP Servers in Claude Desktop

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

**Configuration:**
```json
{
  "mcpServers": {
    "google": {
      "command": "ssh",
      "args": [
        "root@192.168.1.32",
        "pct exec 200 -- docker exec -i mcp-google python /app/server.py"
      ]
    },
    "hydraulic": {
      "command": "ssh",
      "args": [
        "root@192.168.1.32",
        "pct exec 200 -- docker exec -i mcp-hydraulic python /app/server.py"
      ]
    }
  }
}
```

**Note:** This requires SSH access from your desktop to the Proxmox host.

#### 3. Alternative: Local Port Forwarding

If SSH direct connection doesn't work, use port forwarding:

**From your desktop:**
```bash
# Forward Google service
ssh -L 3004:192.168.1.19:3004 root@192.168.1.32

# Forward Hydraulic service
ssh -L 3012:192.168.1.19:3012 root@192.168.1.32
```

Then configure Claude Desktop to connect to `localhost:3004` and `localhost:3012`.

**Note:** Stdio-based servers may not work with port forwarding. You may need to convert them to HTTP first.

---

## Option B: Set Up HTTP API + Mobile Access

To access from mobile, you need to:
1. Convert MCP servers from stdio to HTTP
2. Set up Cloudflare tunnel for external access
3. Use Claude mobile app with HTTP endpoints

### Why This Is Needed
- MCP servers currently use **stdio** (standard input/output)
- Mobile apps need **HTTP/HTTPS** endpoints
- Stdio servers can't be accessed over the network

### What Needs to Change

**Current Architecture:**
```
Claude Desktop → SSH → Stdio MCP Server
```

**Needed Architecture:**
```
Claude Mobile → HTTPS (Cloudflare) → HTTP MCP Server
```

### Implementation Steps

#### 1. Convert Services to HTTP

Each service needs to expose HTTP endpoints. Example for Google service:

**Add to `mcp/google/server.py`:**
```python
from fastapi import FastAPI
import uvicorn

# Create FastAPI app
http_app = FastAPI()

@http_app.get("/health")
async def health():
    return {"status": "ok", "service": "google"}

@http_app.post("/mcp")
async def mcp_endpoint(request: dict):
    # Forward to MCP server logic
    return await handle_mcp_request(request)

if __name__ == "__main__":
    # Check if HTTP mode
    if os.getenv("MCP_TRANSPORT") == "http":
        uvicorn.run(http_app, host="0.0.0.0", port=3000)
    else:
        # Original stdio mode
        asyncio.run(main())
```

**Update docker-compose.autosapien.yml:**
```yaml
environment:
  - MCP_TRANSPORT=http  # Enable HTTP mode
```

#### 2. Set Up Cloudflare Tunnel

**On Container 200:**
```bash
# Install cloudflared (if not already installed)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared.deb

# Create tunnel
cloudflared tunnel create mcp-services

# Configure tunnel
nano ~/.cloudflared/config.yml
```

**Tunnel Configuration:**
```yaml
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: google.autosapien.ai
    service: http://localhost:3004

  - hostname: hydraulic.autosapien.ai
    service: http://localhost:3012

  - hostname: icloud.autosapien.ai
    service: http://localhost:3009

  - hostname: todoist.autosapien.ai
    service: http://localhost:3005

  - hostname: outlook.autosapien.ai
    service: http://localhost:3010

  - hostname: integrator.autosapien.ai
    service: http://localhost:3011

  - service: http_status:404
```

**Add DNS Records:**
```bash
cloudflared tunnel route dns mcp-services google.autosapien.ai
cloudflared tunnel route dns mcp-services hydraulic.autosapien.ai
# etc...
```

**Start Tunnel:**
```bash
cloudflared tunnel run mcp-services
```

#### 3. Access from Claude Mobile

**Current Problem:** Claude mobile app doesn't have built-in MCP support yet.

**Workarounds:**
1. **Use Claude API** - Make HTTP requests to your MCP endpoints, then paste responses into Claude chat
2. **Wait for MCP Mobile Support** - Anthropic may add this feature in the future
3. **Build Custom App** - Create a mobile app that connects to your MCP servers

---

## Recommended Approach: Use Claude Desktop

**Why:**
- MCP protocol fully supported
- No code changes needed
- Can use stdio servers directly
- Better security (SSH tunnels)

**Mobile Access:**
For now, use Claude mobile for general tasks and Claude Desktop when you need MCP server integration.

---

## Quick Decision Guide

**Want to use MCP servers TODAY?**
→ Use Claude Desktop App (Option A)

**Need mobile access?**
→ Wait for Anthropic to add MCP support to mobile app
→ OR convert services to HTTP and use Claude API (significant work)

**Just testing?**
→ Use Claude Desktop with SSH tunnel (easiest)

---

## Current Best Practice

1. **Desktop:** Use Claude Desktop App with MCP configuration
2. **Mobile:** Use regular Claude app (no MCP features yet)
3. **Development:** Test locally with MCP client tools

**When Anthropic adds MCP support to mobile:**
Then set up Cloudflare tunnel for external HTTPS access.

---

## What's Actually Ready Right Now

**For Claude Desktop:**
✅ mcp-google - Ready to configure
✅ mcp-hydraulic - Ready to configure

**For Claude Mobile:**
❌ Not supported yet - no MCP protocol support in mobile app

**For HTTP API Access:**
❌ Need to convert stdio servers to HTTP first

---

## Summary

**Bottom Line:**
- Your MCP servers are deployed and working
- Claude Desktop can connect to them via SSH/stdio
- Claude Mobile cannot use them directly (no MCP support yet)
- To use from mobile, you'd need significant architecture changes

**Recommendation:**
Use Claude Desktop App for MCP features. Use mobile app for regular Claude conversations.
