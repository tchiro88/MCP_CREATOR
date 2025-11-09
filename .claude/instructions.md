# MCP_CREATOR - Claude Code Deployment Instructions

## Project Overview

This is a self-hosted MCP (Model Context Protocol) connector infrastructure project with 7 production-ready connectors. The goal is to deploy these MCP servers to a Proxmox LXC container with remote access via an existing Cloudflare Tunnel.

## Important Context

### Existing Infrastructure
- ✅ **Cloudflare Tunnel LXC already exists** - All tunnel routes should go through this existing setup
- ✅ **Google OAuth credentials available** - User has `credentials.json` and `token.json` ready
- ⏸️  **Other service credentials** - User will provide as needed (ask before proceeding)

### Available MCP Connectors (7 total)
1. **GitHub** - Repos, Issues, PRs (requires: GITHUB_TOKEN)
2. **Google** - Gmail, Drive, Calendar (requires: credentials.json + token.json) ✅ USER HAS THESE
3. **Todoist** - Task management (requires: TODOIST_API_TOKEN)
4. **Home Assistant** - Smart home (requires: HA_URL + HA_TOKEN)
5. **Notion** - Databases, pages (requires: NOTION_TOKEN)
6. **Slack** - Messages, channels (requires: SLACK_BOT_TOKEN)
7. **iCloud** - Mail, calendar, contacts (requires: ICLOUD_USERNAME + ICLOUD_PASSWORD)

## Key Documentation Files

- **[DEPLOYMENT-GUIDE.md](../DEPLOYMENT-GUIDE.md)** - Complete step-by-step deployment guide
- **[CREDENTIALS-GUIDE.md](../CREDENTIALS-GUIDE.md)** - How to obtain all credentials
- **[QUICKSTART-MINIMAL.md](../QUICKSTART-MINIMAL.md)** - Quick minimal setup
- **Individual connector docs**: `mcp/*/README.md`

## Deployment Strategy

### 1. Pre-Deployment Assessment
When starting deployment work:

**Ask the user:**
- "Which MCP connectors do you want to deploy? (You have Google credentials ready)"
- "What is the IP address of your existing Cloudflare Tunnel LXC?"
- "What is the IP address of your Proxmox host?"
- "What LXC container ID should I use for the MCP servers?"
- "What domain name will be used for the MCP endpoints?"

**Note:** User has Google OAuth credentials ready to be copied. For other services, STOP and ask for credentials before proceeding with that connector's deployment.

### 2. Use Available Agents

**IMPORTANT:** Use the Task tool with specialized agents to streamline work:

```
When exploring the codebase or gathering information:
- Use Task tool with subagent_type="Explore" for codebase exploration
- Use Task tool with subagent_type="Plan" for planning deployment steps

Example:
"I need to understand the docker-compose configuration structure"
→ Use Task agent (Explore) instead of direct Grep/Read
```

### 3. Credential Handling Workflow

**For Google Services** (credentials available):
```
1. Ask user: "Please provide your Google credentials.json and token.json files"
2. Wait for user to paste/upload files
3. Use Write tool to create:
   - deployment/credentials/google/credentials.json
   - deployment/credentials/google/token.json
4. Set permissions: chmod 600 on both files
```

**For Other Services** (as needed):
```
1. STOP before deploying each connector
2. Ask user: "To deploy [SERVICE], I need [CREDENTIAL_TYPE]. Do you have this ready?"
3. Wait for user response
4. If yes: Get credential and add to deployment/.env
5. If no: Skip this connector and move to next
```

### 4. Cloudflare Tunnel Configuration

**User has existing Cloudflare Tunnel LXC** - Do NOT create new tunnel:

```
1. Ask for existing tunnel LXC IP
2. Ask for tunnel name/ID if needed
3. Configure DNS routes to point to new MCP server LXC
4. Update tunnel config to route subdomains to MCP LXC IP:PORT
   - github.domain.com → MCP_LXC_IP:3001
   - google.domain.com → MCP_LXC_IP:3004
   - todoist.domain.com → MCP_LXC_IP:3005
   - etc.
```

### 5. Deployment Steps (High-Level)

Follow **DEPLOYMENT-GUIDE.md** but adapt for existing tunnel:

**Phase 1: Prepare Credentials**
1. Collect which connectors user wants
2. For Google: Get credentials.json + token.json from user
3. For others: Ask and collect as needed
4. Create deployment/.env file with all tokens

**Phase 2: Setup MCP LXC**
1. Create Proxmox LXC container
2. Install Docker + Docker Compose
3. Clone repository
4. Copy credentials from development machine

**Phase 3: Configure Tunnel Routes** (use existing tunnel)
1. Get existing tunnel info from user
2. Add DNS routes for each connector
3. Update tunnel config with new routes
4. Restart tunnel service

**Phase 4: Deploy & Test**
1. Build and start Docker containers
2. Test local connectivity
3. Test remote access via tunnel
4. Configure Claude apps

### 6. SSH File Transfer

When copying credentials to Proxmox, offer user three options:

**Option 1: Via Proxmox Host** (recommended)
```bash
# From user's laptop to Proxmox host
scp deployment/.env root@proxmox-ip:/tmp/mcp-env
scp -r deployment/credentials root@proxmox-ip:/tmp/mcp-credentials

# From Proxmox host to LXC
pct push [LXC_ID] /tmp/mcp-env /opt/MCP_CREATOR/deployment/.env
pct push [LXC_ID] /tmp/mcp-credentials /opt/MCP_CREATOR/deployment/credentials -r
```

**Option 2: Direct to LXC** (if SSH enabled)
```bash
scp deployment/.env root@lxc-ip:/opt/MCP_CREATOR/deployment/
scp -r deployment/credentials root@lxc-ip:/opt/MCP_CREATOR/deployment/
```

**Option 3: Manual paste** (for small files)
- Provide file contents to user
- User pastes into terminal on target system

## Common Commands Reference

### Proxmox Host Commands
```bash
# Create LXC
pct create [ID] [template] --hostname mcp-server --memory 4096 --cores 2

# Start/Stop LXC
pct start [ID]
pct stop [ID]

# Enter LXC
pct enter [ID]

# Push files to LXC
pct push [ID] [source] [destination]

# Execute command in LXC
pct exec [ID] -- [command]
```

### Inside MCP LXC
```bash
# Navigate to deployment
cd /opt/MCP_CREATOR/deployment

# Start services
docker-compose -f docker-compose.minimal.yml up -d --build

# View logs
docker-compose -f docker-compose.minimal.yml logs -f

# Restart services
docker-compose -f docker-compose.minimal.yml restart

# Check status
docker-compose -f docker-compose.minimal.yml ps
```

### Cloudflare Tunnel LXC
```bash
# Add DNS route
cloudflared tunnel route dns [tunnel-name] [subdomain.domain.com]

# View tunnel config
cat /etc/cloudflared/config.yml

# Restart tunnel
systemctl restart cloudflared

# Check status
systemctl status cloudflared
```

## Error Handling

### If credentials are missing:
```
STOP deployment of that connector
Ask user: "To proceed with [SERVICE], I need [CREDENTIAL].
Would you like to:
1. Provide the credential now
2. Skip this connector
3. See instructions on how to obtain it (CREDENTIALS-GUIDE.md)"
```

### If tunnel connection fails:
```
1. Verify tunnel LXC can reach MCP LXC (ping test)
2. Check port mappings in docker-compose
3. Verify DNS routes in Cloudflare
4. Check tunnel config ingress rules
```

### If container won't start:
```
1. Check logs: docker-compose logs [container-name]
2. Verify .env file has required variables
3. Check credential file permissions (should be 600)
4. Verify credential files exist in correct locations
```

## Expected File Structure After Deployment

```
/opt/MCP_CREATOR/
├── deployment/
│   ├── .env                          # All environment variables
│   ├── credentials/
│   │   └── google/
│   │       ├── credentials.json      # Google OAuth client
│   │       └── token.json           # Google auth token
│   ├── docker-compose.minimal.yml
│   └── [other config files]
├── mcp/
│   ├── github/
│   ├── google/
│   ├── todoist/
│   ├── homeassistant/
│   ├── notion/
│   ├── slack/
│   └── icloud/
└── [other project files]
```

## Port Mappings

| Connector | Internal | LXC External | Cloudflare Route |
|-----------|----------|--------------|------------------|
| GitHub | 3000 | 3001 | github.domain.com |
| Google | 3000 | 3004 | google.domain.com |
| Todoist | 3000 | 3005 | todoist.domain.com |
| Home Assistant | 3000 | 3006 | ha.domain.com |
| Notion | 3000 | 3007 | notion.domain.com |
| Slack | 3000 | 3008 | slack.domain.com |
| iCloud | 3000 | 3009 | icloud.domain.com |

## Testing Checklist

After deployment, verify:

- [ ] All containers running: `docker-compose ps`
- [ ] Local connectivity: `curl http://localhost:3001/health`
- [ ] Tunnel connectivity: `curl https://github.domain.com/health`
- [ ] DNS resolution: `nslookup github.domain.com`
- [ ] Claude app connection: Ask Claude "List available MCP servers"

## Remember

1. **Always ask before proceeding** if credentials are needed
2. **Use existing Cloudflare Tunnel LXC** - don't create a new one
3. **Use Task agents** for exploration and planning to save context
4. **Follow DEPLOYMENT-GUIDE.md** as the source of truth
5. **User has Google credentials ready** - ask for them first
6. **Stop and ask for other credentials** as each connector is deployed

## Quick Start Command

When user says "deploy MCP servers", respond with:

```
I'll help you deploy the MCP servers to your Proxmox environment using your existing Cloudflare Tunnel.

First, let me gather some information:

1. Which MCP connectors would you like to deploy?
   Available: GitHub, Google ✅, Todoist, Home Assistant, Notion, Slack, iCloud

2. What is your Proxmox host IP address?
3. What is your existing Cloudflare Tunnel LXC IP address?
4. What LXC container ID should I use for the new MCP servers?
5. What domain will be used for MCP endpoints?

I have your Google credentials ready to copy. I'll ask for other credentials as needed.
```

---

**This file is automatically read by Claude Code when working in this project directory.**
