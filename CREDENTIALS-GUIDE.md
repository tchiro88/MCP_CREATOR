# Credentials Setup Guide

Quick reference for getting credentials for all 7 MCP connectors.

## 🚀 Quick Copy - If You Already Have Credentials

**If you already have all credentials on your laptop and just need to copy them to the server:**

```bash
# From your laptop, copy .env and credentials to Proxmox LXC
scp deployment/.env root@your-proxmox-lxc-ip:/opt/MCP_CREATOR/deployment/
scp -r deployment/credentials/ root@your-proxmox-lxc-ip:/opt/MCP_CREATOR/deployment/

# Or if you need to go through Proxmox host first:
scp deployment/.env root@proxmox-host:/tmp/
scp -r deployment/credentials/ root@proxmox-host:/tmp/

# Then on Proxmox host, push to LXC (container ID 200):
pct push 200 /tmp/.env /opt/MCP_CREATOR/deployment/.env
pct push 200 /tmp/credentials /opt/MCP_CREATOR/deployment/credentials -r
```

**That's it!** Skip to "Deploy" section if all your credentials are already configured.

---

## Google Services (Gmail, Drive, Calendar)

### What You Need
- Google account
- OAuth 2.0 credentials (credentials.json)
- Authenticated token (token.json)

### Step-by-Step

1. **Create Google Cloud Project**
   - Go to: https://console.cloud.google.com/
   - Click "New Project"
   - Name: "MCP Connectors"

2. **Enable APIs**
   - Navigate to: **APIs & Services** → **Library**
   - Search and enable:
     - Gmail API
     - Google Drive API
     - Google Calendar API

3. **Create OAuth Credentials**
   - Go to: **APIs & Services** → **Credentials**
   - Click: **Create Credentials** → **OAuth client ID**
   - Configure consent screen if prompted (Internal is fine)
   - Application type: **Desktop app**
   - Name: "MCP Server"
   - Click: **Create**

4. **Download Credentials**
   - Click download icon (⬇️) next to your OAuth client
   - Save as `credentials.json`

5. **Authenticate**
   ```bash
   # On your local machine (NOT in Proxmox yet!)
   cd MCP_CREATOR/mcp/google
   pip install -r requirements.txt

   # Copy credentials.json to this directory
   cp ~/Downloads/credentials.json .

   # Run to authenticate (opens browser)
   python server.py
   ```

   This creates `token.json` - your authenticated session

6. **Copy to Proxmox**
   ```bash
   # Copy both files to your Proxmox LXC
   scp credentials.json token.json root@proxmox:/tmp/

   # On Proxmox, copy into LXC
   pct push 101 /tmp/credentials.json /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/credentials.json
   pct push 101 /tmp/token.json /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/token.json
   ```

**Security**:
- `credentials.json` = OAuth client config (semi-sensitive)
- `token.json` = Your authenticated session (VERY sensitive!)
- Never commit these to Git!
- `token.json` expires after ~7 days of inactivity (will auto-refresh if refresh token valid)

---

## Todoist

### What You Need
- Todoist account (free or premium)
- API token

### Step-by-Step

1. **Get API Token**
   - Log in to Todoist web app
   - Go to: https://todoist.com/prefs/integrations
   - Scroll to: **API token** section
   - Copy your token

   Token format: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0`

2. **Add to .env File**
   ```bash
   # In your deployment directory
   cd deployment
   nano .env
   ```

   Add:
   ```bash
   TODOIST_API_TOKEN=your-token-here
   ```

**Security**:
- This token gives FULL access to your Todoist account
- Treat it like a password
- You can revoke and regenerate it anytime from Todoist settings

---

## GitHub

### What You Need
- GitHub account
- Personal Access Token (PAT)

### Step-by-Step

1. **Create Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Click: **Generate new token** → **Generate new token (classic)**
   - Note: "MCP Server Access"
   - Expiration: Choose your preference (90 days recommended)
   - Select scopes:
     - ✅ `repo` (Full repository access)
     - ✅ `read:user` (Read user profile data)
     - ✅ `write:repo_hook` (Manage webhooks)
   - Click: **Generate token**

2. **Copy Token**
   - Copy immediately (you won't see it again!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

3. **Add to .env File**
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```

**Security**:
- Token has full access to your repos based on scopes
- Can revoke anytime from GitHub settings
- Set expiration and rotate regularly

---

## Home Assistant

### What You Need
- Home Assistant instance running
- Long-lived access token

### Step-by-Step

1. **Log into Home Assistant**
   - Go to your HA instance (e.g., http://homeassistant.local:8123)
   - Log in with your account

2. **Create Long-Lived Access Token**
   - Click your profile (bottom left)
   - Scroll to: **Long-Lived Access Tokens**
   - Click: **Create Token**
   - Name: "MCP Server"
   - Click: **OK**

3. **Copy Token**
   - Token shown only once!
   - Format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (very long)

4. **Add to .env File**
   ```bash
   HA_URL=http://homeassistant.local:8123
   HA_TOKEN=eyJhbGci...your-token-here
   ```

**Security**:
- Token gives FULL access to control all Home Assistant devices
- Can revoke from HA profile anytime
- Token doesn't expire unless manually revoked

---

## Notion

### What You Need
- Notion workspace
- Integration token

### Step-by-Step

1. **Create Notion Integration**
   - Go to: https://www.notion.so/my-integrations
   - Click: **+ New integration**
   - Name: "MCP Server"
   - Associated workspace: Select your workspace
   - Type: Internal integration
   - Click: **Submit**

2. **Copy Integration Token**
   - After creation, click: **Show** then **Copy**
   - Format: `secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

3. **Share Databases/Pages with Integration**
   - Open each database or page you want MCP to access
   - Click **•••** (top right) → **Connections**
   - Click **Add connections**
   - Search for "MCP Server" and select it
   - **Important**: Integration can only access what you explicitly share!

4. **Add to .env File**
   ```bash
   NOTION_TOKEN=secret_your_token_here
   ```

**Security**:
- Integration only accesses databases/pages you share with it
- Can revoke from https://www.notion.so/my-integrations
- Use principle of least privilege (only share what's needed)

---

## Slack

### What You Need
- Slack workspace (admin or ability to add apps)
- Bot user OAuth token

### Step-by-Step

1. **Create Slack App**
   - Go to: https://api.slack.com/apps
   - Click: **Create New App** → **From scratch**
   - App Name: "MCP Server"
   - Workspace: Select your workspace
   - Click: **Create App**

2. **Add Bot Token Scopes**
   - Navigate to: **OAuth & Permissions** (left sidebar)
   - Scroll to: **Bot Token Scopes**
   - Click: **Add an OAuth Scope**
   - Add these scopes:
     - `channels:history`, `channels:read`, `channels:write`
     - `groups:history`, `groups:read`, `groups:write`
     - `im:history`, `im:read`, `im:write`
     - `mpim:history`, `mpim:read`, `mpim:write`
     - `chat:write`
     - `files:read`, `files:write`
     - `reactions:read`, `reactions:write`
     - `search:read`
     - `users:read`, `users:read.email`

3. **Install to Workspace**
   - Scroll to top of **OAuth & Permissions**
   - Click: **Install to Workspace**
   - Review permissions → **Allow**

4. **Copy Bot Token**
   - After install, you'll see: **Bot User OAuth Token**
   - Format: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`
   - Copy this token

5. **Add to .env File**
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-token-here
   ```

**Security**:
- Token gives bot access to workspace based on scopes
- Can revoke by uninstalling app
- Regenerate token from app settings if compromised

---

## iCloud

### What You Need
- Apple ID with iCloud account
- **App-specific password** (NOT regular Apple ID password!)

### Step-by-Step

1. **Generate App-Specific Password**
   - Go to: https://appleid.apple.com/account/manage
   - Sign in with your Apple ID
   - Navigate to: **Security** section
   - Click: **App-Specific Passwords** → **Generate Password**
   - Label: "MCP Server"
   - Click: **Create**

2. **Copy Password**
   - Format: `xxxx-xxxx-xxxx-xxxx`
   - Copy immediately (can't see again!)
   - Remove dashes when using: `xxxxxxxxxxxxxxxx`

3. **Enable iCloud Services**
   - On iPhone: Settings → [Your Name] → iCloud
   - On Mac: System Settings → Apple ID → iCloud
   - Enable:
     - ✅ iCloud Mail
     - ✅ Calendars
     - ✅ Reminders
     - ✅ iCloud Drive
     - ✅ Contacts

4. **Add to .env File**
   ```bash
   ICLOUD_USERNAME=your-apple-id@icloud.com
   ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

**Security**:
- **NEVER use regular Apple ID password** - only app-specific!
- App-specific passwords are for third-party apps only
- Can revoke from Apple ID settings anytime
- Each app/device should have its own password
- If compromised, revoke that password specifically

---

## Cloudflare Tunnel

### What You Need
- Cloudflare account (free)
- Domain name added to Cloudflare
- Cloudflared installed on your Proxmox LXC

### Step-by-Step

1. **Install cloudflared**
   ```bash
   # On your Cloudflare Tunnel LXC
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   dpkg -i cloudflared-linux-amd64.deb
   ```

2. **Authenticate**
   ```bash
   cloudflared tunnel login
   ```
   - Opens browser
   - Select your Cloudflare domain
   - Downloads certificate to `~/.cloudflared/cert.pem`

3. **Create Tunnel**
   ```bash
   cloudflared tunnel create mcp-tunnel
   ```

   Output shows:
   - Tunnel ID: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`
   - Credentials file: `~/.cloudflared/TUNNEL-ID.json`

4. **Get Tunnel Token (Alternative to config file)**
   ```bash
   cloudflared tunnel token mcp-tunnel
   ```

   Copy token to `.env`:
   ```bash
   CLOUDFLARE_TUNNEL_TOKEN=eyJh...long-token...
   ```

5. **Create DNS Routes**
   ```bash
   cloudflared tunnel route dns mcp-tunnel google.yourdomain.com
   cloudflared tunnel route dns mcp-tunnel todoist.yourdomain.com
   cloudflared tunnel route dns mcp-tunnel github.yourdomain.com
   cloudflared tunnel route dns mcp-tunnel files.yourdomain.com
   ```

**Security**:
- Tunnel credentials give access to route traffic through your tunnel
- Keep credentials file secure
- Can delete and recreate tunnel if compromised

---

## Quick Reference - All 7 Connectors

| Service | Credential Type | Where to Get | Env Variable |
|---------|----------------|--------------|--------------|
| GitHub | Personal Access Token | github.com/settings/tokens | `GITHUB_TOKEN` |
| Google | OAuth files | console.cloud.google.com | Files: credentials.json, token.json |
| Todoist | API Token | todoist.com/prefs/integrations | `TODOIST_API_TOKEN` |
| Home Assistant | Long-lived Token | HA Profile → Tokens | `HA_URL`, `HA_TOKEN` |
| Notion | Integration Token | notion.so/my-integrations | `NOTION_TOKEN` |
| Slack | Bot OAuth Token | api.slack.com/apps | `SLACK_BOT_TOKEN` |
| iCloud | App-Specific Password | appleid.apple.com | `ICLOUD_USERNAME`, `ICLOUD_PASSWORD` |
| Cloudflare | Tunnel Token | `cloudflared tunnel token` | `CLOUDFLARE_TUNNEL_TOKEN` |

---

## Storage Locations

### In Repository (DO NOT COMMIT!)
```
deployment/
├── .env                           # All tokens (gitignored)
│   ├── GITHUB_TOKEN
│   ├── TODOIST_API_TOKEN
│   ├── HA_URL + HA_TOKEN
│   ├── NOTION_TOKEN
│   ├── SLACK_BOT_TOKEN
│   ├── ICLOUD_USERNAME + ICLOUD_PASSWORD
│   └── CLOUDFLARE_TUNNEL_TOKEN
│
└── credentials/
    └── google/
        ├── credentials.json       # Google OAuth client (gitignored)
        └── token.json            # Google session (gitignored)
```

### On Proxmox LXC
```
/opt/MCP_CREATOR/deployment/
├── .env                           # All 7 connectors + Cloudflare
└── credentials/
    └── google/
        ├── credentials.json
        └── token.json
```

### SSH Copy from Laptop to Server

**Method 1: Direct to LXC** (if LXC has SSH):
```bash
# From your laptop
cd /path/to/MCP_CREATOR

# Copy .env file
scp deployment/.env root@lxc-ip:/opt/MCP_CREATOR/deployment/

# Copy Google credentials folder
scp -r deployment/credentials/ root@lxc-ip:/opt/MCP_CREATOR/deployment/

# Set proper permissions
ssh root@lxc-ip "chmod 600 /opt/MCP_CREATOR/deployment/.env"
ssh root@lxc-ip "chmod 600 /opt/MCP_CREATOR/deployment/credentials/google/*"
```

**Method 2: Via Proxmox Host** (recommended):
```bash
# From your laptop to Proxmox host
scp deployment/.env root@proxmox-ip:/tmp/mcp-env
scp -r deployment/credentials/ root@proxmox-ip:/tmp/mcp-credentials/

# SSH into Proxmox host
ssh root@proxmox-ip

# Push to LXC (container ID 200)
pct push 200 /tmp/mcp-env /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- mkdir -p /opt/MCP_CREATOR/deployment/credentials/google
pct push 200 /tmp/mcp-credentials/google/credentials.json /opt/MCP_CREATOR/deployment/credentials/google/
pct push 200 /tmp/mcp-credentials/google/token.json /opt/MCP_CREATOR/deployment/credentials/google/

# Set permissions inside LXC
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/credentials/google/*

# Clean up temp files
rm /tmp/mcp-env
rm -rf /tmp/mcp-credentials/
```

**Method 3: Using rsync** (preserves permissions):
```bash
# From laptop to LXC directly
rsync -avz --progress deployment/.env root@lxc-ip:/opt/MCP_CREATOR/deployment/
rsync -avz --progress deployment/credentials/ root@lxc-ip:/opt/MCP_CREATOR/deployment/credentials/
```

---

## Troubleshooting

### Google: "Token expired"
**Solution**: Delete `token.json` and re-run `python server.py` to re-authenticate

### Todoist: "Unauthorized"
**Solution**: Check your API token hasn't been revoked at https://todoist.com/prefs/integrations

### GitHub: "Bad credentials"
**Solution**: Token might be expired or revoked. Generate a new one.

### Home Assistant: "Connection refused"
**Solution**: Check HA_URL is correct and accessible from LXC. Test: `curl $HA_URL/api/`

### Notion: "Could not find database"
**Solution**: Make sure you shared the database with your MCP Server integration

### Slack: "missing_scope"
**Solution**: Add the missing scope in app settings, reinstall app, use new token

### iCloud: "Two-factor authentication required"
**Solution**: Use app-specific password, NOT your regular Apple ID password!

### Cloudflare: "Tunnel not connecting"
**Solution**: Check tunnel status with `cloudflared tunnel info mcp-tunnel`

---

## Security Best Practices

1. ✅ Never commit credentials to Git (already in .gitignore)
2. ✅ Use environment variables for tokens
3. ✅ Set file permissions: `chmod 600` for credential files
4. ✅ Rotate tokens regularly (every 90 days minimum)
5. ✅ Use Cloudflare Zero Trust to add authentication layer
6. ✅ Monitor access logs for suspicious activity
7. ✅ Backup credentials securely (encrypted)
8. ✅ Use different credentials for dev/prod if possible

---

## Need Help?

- **GitHub**: See `mcp/github/README.md`
- **Google OAuth**: See `mcp/google/README.md`
- **Todoist**: See `mcp/todoist/README.md`
- **Home Assistant**: See `mcp/homeassistant/README.md`
- **Notion**: See `mcp/notion/README.md`
- **Slack**: See `mcp/slack/README.md`
- **iCloud**: See `mcp/icloud/README.md`
- **Deployment**: See `deployment/DEPLOYMENT-COMPLETE.md`

---

## Complete .env File Example

```bash
# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=eyJhxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Todoist
TODOIST_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Home Assistant
HA_URL=http://homeassistant.local:8123
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx

# iCloud
ICLOUD_USERNAME=your-apple-id@icloud.com
ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Google: Uses file-based credentials
# (no env vars, just files in credentials/google/)
```

---

**Ready to deploy?** Follow the [Complete Deployment Guide](deployment/DEPLOYMENT-COMPLETE.md)!
