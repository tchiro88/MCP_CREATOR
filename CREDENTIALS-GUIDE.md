# Credentials Setup Guide

Quick reference for getting credentials for each MCP connector.

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

## GitHub (Optional)

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

## Quick Reference

| Service | Credential Type | Where to Get | Env Variable |
|---------|----------------|--------------|--------------|
| Google | OAuth files | console.cloud.google.com | Files: credentials.json, token.json |
| Todoist | API Token | todoist.com/prefs/integrations | `TODOIST_API_TOKEN` |
| GitHub | Personal Access Token | github.com/settings/tokens | `GITHUB_TOKEN` |
| Cloudflare | Tunnel Token | `cloudflared tunnel token` | `CLOUDFLARE_TUNNEL_TOKEN` |

---

## Storage Locations

### In Repository (DO NOT COMMIT!)
```
deployment/
├── .env                           # All tokens (gitignored)
└── credentials/
    └── google/
        ├── credentials.json       # Google OAuth client (gitignored)
        └── token.json            # Google session (gitignored)
```

### On Proxmox LXC
```
/opt/mcp-servers/MCP_CREATOR/deployment/
├── .env
└── credentials/
    └── google/
        ├── credentials.json
        └── token.json
```

---

## Troubleshooting

### Google: "Token expired"
**Solution**: Delete `token.json` and re-run `python server.py` to re-authenticate

### Todoist: "Unauthorized"
**Solution**: Check your API token hasn't been revoked at https://todoist.com/prefs/integrations

### GitHub: "Bad credentials"
**Solution**: Token might be expired or revoked. Generate a new one.

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

- **Google OAuth**: See `mcp/google/README.md`
- **Todoist**: See `mcp/todoist/README.md`
- **Deployment**: See `deployment/PROXMOX-SETUP.md`
- **Quick Start**: See `QUICKSTART-MINIMAL.md`

---

**Ready to deploy?** Follow the [Proxmox Setup Guide](deployment/PROXMOX-SETUP.md)!
