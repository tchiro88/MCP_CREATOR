# MCP Deployment on Proxmox LXC

Complete guide for deploying MCP connectors in your Proxmox environment with separate LXC containers.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Proxmox Host                              │
│                                                                   │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐ │
│  │   LXC: MCP Servers           │  │  LXC: Cloudflare Tunnel  │ │
│  │   (Debian)                   │  │  (Debian)                │ │
│  │                              │  │                          │ │
│  │  ┌────────────────────────┐  │  │  ┌────────────────────┐ │ │
│  │  │ Docker Containers:     │  │  │  │   cloudflared      │ │ │
│  │  │ • mcp-google   :3004   │  │  │  │   (tunnel daemon)  │ │ │
│  │  │ • mcp-todoist  :3005   │  │  │  └────────────────────┘ │ │
│  │  │ • mcp-github   :3001   │◀─┼──┤                          │ │
│  │  │ • mcp-filesystem:3002  │  │  │                          │ │
│  │  └────────────────────────┘  │  │                          │ │
│  └──────────────────────────────┘  └───────────┬──────────────┘ │
│                                                 │                 │
└─────────────────────────────────────────────────┼─────────────────┘
                                                  │
                                    Cloudflare Encrypted Tunnel
                                                  │
                                    ┌─────────────▼──────────────┐
                                    │   Cloudflare Edge Network  │
                                    └─────────────┬──────────────┘
                                                  │ HTTPS
                                    ┌─────────────▼──────────────┐
                                    │  Your Devices:             │
                                    │  • iPhone                  │
                                    │  • Laptop                  │
                                    │  • Any device              │
                                    └────────────────────────────┘
```

## LXC Setup

### LXC 1: MCP Servers (Debian)

```bash
# Create Debian LXC on Proxmox
pct create 101 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname mcp-servers \
  --memory 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Start LXC
pct start 101

# Enter LXC
pct enter 101
```

**Inside the LXC:**

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
apt install -y curl git
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install -y docker-compose

# Create project directory
mkdir -p /opt/mcp-servers
cd /opt/mcp-servers

# Clone MCP_CREATOR repo (or copy files)
git clone https://github.com/tchiro88/MCP_CREATOR.git
cd MCP_CREATOR/deployment
```

### LXC 2: Cloudflare Tunnel (Debian)

```bash
# Create Debian LXC on Proxmox
pct create 102 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname cloudflare-tunnel \
  --memory 512 \
  --cores 1 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Start LXC
pct start 102

# Enter LXC
pct enter 102
```

**Inside the LXC:**

```bash
# Update system
apt update && apt upgrade -y

# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

## Credentials Setup

### 1. Google Services (Gmail, Drive, Calendar)

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "MCP Connectors"
3. Enable APIs:
   - Gmail API
   - Google Drive API
   - Google Calendar API

#### Step 2: Create OAuth Credentials

1. **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "MCP Server"
5. **Download JSON** → save as `credentials.json`

#### Step 3: Authenticate Locally

**On your laptop/desktop (not in LXC):**

```bash
# Clone the repo
git clone https://github.com/tchiro88/MCP_CREATOR.git
cd MCP_CREATOR/mcp/google

# Install dependencies
pip install -r requirements.txt

# Copy credentials.json here
cp ~/Downloads/credentials.json .

# Run server to authenticate
python server.py
```

This will:
- Open your browser
- Ask for Google permissions
- Create `token.json` (your authenticated session)

#### Step 4: Copy to Proxmox LXC

```bash
# On your laptop, copy credentials to Proxmox LXC
scp credentials.json token.json root@proxmox-host:/tmp/

# On Proxmox host
pct push 101 /tmp/credentials.json /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/credentials.json
pct push 101 /tmp/token.json /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/token.json

# Set permissions
pct exec 101 -- chmod 600 /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/token.json
```

### 2. Todoist

#### Step 1: Get API Token

1. Go to [Todoist Settings → Integrations](https://todoist.com/prefs/integrations)
2. Scroll to **API token** section
3. Copy your token (looks like: `a1b2c3d4e5f6g7h8i9j0...`)

#### Step 2: Add to .env File

**In your MCP Servers LXC:**

```bash
cd /opt/mcp-servers/MCP_CREATOR/deployment

# Create .env from example
cp .env.minimal.example .env

# Edit .env
nano .env
```

Add your token:
```bash
TODOIST_API_TOKEN=a1b2c3d4e5f6g7h8i9j0...
```

### 3. GitHub (Optional)

1. Go to [GitHub Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. **Generate new token (classic)**
3. Select scopes: `repo`, `read:user`
4. Copy token

Add to `.env`:
```bash
GITHUB_TOKEN=ghp_your_github_token_here
```

## Cloudflare Tunnel Setup

### Step 1: Create Tunnel

**In your Cloudflare Tunnel LXC:**

```bash
# Authenticate with Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create mcp-tunnel

# Note the tunnel ID that's displayed
# Example: Created tunnel mcp-tunnel with id a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
```

### Step 2: Configure DNS Routes

```bash
# Route domains to tunnel (replace yourdomain.com with your domain)
cloudflared tunnel route dns mcp-tunnel google.yourdomain.com
cloudflared tunnel route dns mcp-tunnel todoist.yourdomain.com
cloudflared tunnel route dns mcp-tunnel github.yourdomain.com
cloudflared tunnel route dns mcp-tunnel files.yourdomain.com
```

### Step 3: Create Tunnel Configuration

```bash
# Create config directory
mkdir -p /etc/cloudflared

# Copy example config
# (Get this from your MCP_CREATOR repo)
nano /etc/cloudflared/config.yml
```

**Config content** (replace `YOUR-TUNNEL-ID` with your actual tunnel ID):

```yaml
tunnel: YOUR-TUNNEL-ID-HERE
credentials-file: /root/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  # Google Services MCP
  - hostname: google.yourdomain.com
    service: http://MCP-SERVERS-LXC-IP:3004

  # Todoist MCP
  - hostname: todoist.yourdomain.com
    service: http://MCP-SERVERS-LXC-IP:3005

  # GitHub MCP
  - hostname: github.yourdomain.com
    service: http://MCP-SERVERS-LXC-IP:3001

  # Filesystem MCP
  - hostname: files.yourdomain.com
    service: http://MCP-SERVERS-LXC-IP:3002

  # Catch-all
  - service: http_status:404
```

**Important**: Replace `MCP-SERVERS-LXC-IP` with the actual IP address of your MCP Servers LXC (e.g., `192.168.1.101`)

### Step 4: Start Tunnel as Service

```bash
# Install as systemd service
cloudflared service install

# Start service
systemctl start cloudflared
systemctl enable cloudflared

# Check status
systemctl status cloudflared
```

## Deploy MCP Servers

**In your MCP Servers LXC:**

```bash
cd /opt/mcp-servers/MCP_CREATOR/deployment

# Create credentials directory for Google
mkdir -p credentials/google

# Verify .env file is configured
cat .env

# Build and start containers
docker-compose -f docker-compose.minimal.yml up -d

# Check logs
docker-compose -f docker-compose.minimal.yml logs -f

# Verify containers are running
docker-compose -f docker-compose.minimal.yml ps
```

## Testing

### Test from LXC

```bash
# Test Google MCP
curl http://localhost:3004/health

# Test Todoist MCP
curl http://localhost:3005/health
```

### Test from Internet

```bash
# From your laptop/phone
curl https://google.yourdomain.com/health
curl https://todoist.yourdomain.com/health
```

## Configure Claude Apps

### Claude Desktop (Laptop)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or: `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "google": {
      "url": "https://google.yourdomain.com",
      "transport": "http"
    },
    "todoist": {
      "url": "https://todoist.yourdomain.com",
      "transport": "http"
    },
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

Restart Claude Desktop.

### Claude iPhone App

1. Open Claude app
2. Settings → Integrations → Add MCP Server
3. Add each server:
   - Name: Google Services
   - URL: `https://google.yourdomain.com`

   Repeat for Todoist, GitHub, Files

### Claude Code (Any Machine)

Edit: `~/.config/claude-code/config.json`

```json
{
  "mcpServers": {
    "google": {
      "url": "https://google.yourdomain.com",
      "transport": "http"
    },
    "todoist": {
      "url": "https://todoist.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Security: Cloudflare Zero Trust

### Add Authentication

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. **Access** → **Applications** → **Add an application**
3. Select: **Self-hosted**
4. Configuration:
   - Application name: "MCP Servers"
   - Session duration: 24 hours
   - Application domain: `*.yourdomain.com` (wildcard)

5. **Add policy**:
   - Policy name: "Allow My Email"
   - Action: Allow
   - Include: `Emails: your-email@gmail.com`

6. Save

Now accessing any MCP server will require authentication once per 24 hours.

## Troubleshooting

### Google MCP won't start

**Problem**: "Credentials file not found"

**Solution**:
```bash
# Verify credentials exist
pct exec 101 -- ls -la /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/

# Should see:
# credentials.json
# token.json

# If missing, copy them from your laptop (see Credentials Setup)
```

### Todoist MCP fails

**Problem**: "TODOIST_API_TOKEN not set"

**Solution**:
```bash
# Check .env file
pct exec 101 -- cat /opt/mcp-servers/MCP_CREATOR/deployment/.env | grep TODOIST

# If empty, add your token
pct exec 101 -- nano /opt/mcp-servers/MCP_CREATOR/deployment/.env
```

### Cloudflare Tunnel not connecting

**Problem**: Tunnel status shows disconnected

**Solution**:
```bash
# On Cloudflare Tunnel LXC, check logs
journalctl -u cloudflared -f

# Verify MCP Servers LXC IP is correct in config
cat /etc/cloudflared/config.yml

# Test connectivity from tunnel LXC to MCP LXC
ping MCP-SERVERS-LXC-IP
curl http://MCP-SERVERS-LXC-IP:3004/health
```

### Can't access from iPhone

**Problem**: Connection refused or timeout

**Checklist**:
1. ✅ Cloudflare Tunnel running? `systemctl status cloudflared`
2. ✅ DNS records created? Check Cloudflare dashboard
3. ✅ MCP containers running? `docker-compose ps`
4. ✅ Firewall blocking? Check Proxmox/LXC firewall rules

## Maintenance

### Update MCP Servers

```bash
# Pull latest code
cd /opt/mcp-servers/MCP_CREATOR
git pull

# Rebuild and restart
cd deployment
docker-compose -f docker-compose.minimal.yml down
docker-compose -f docker-compose.minimal.yml up -d --build
```

### View Logs

```bash
# All containers
docker-compose -f docker-compose.minimal.yml logs -f

# Specific container
docker-compose -f docker-compose.minimal.yml logs -f mcp-google
docker-compose -f docker-compose.minimal.yml logs -f mcp-todoist
```

### Backup Credentials

```bash
# Backup Google credentials
pct exec 101 -- tar -czf /tmp/google-creds-backup.tar.gz \
  /opt/mcp-servers/MCP_CREATOR/deployment/credentials/google/

# Copy to Proxmox host
pct pull 101 /tmp/google-creds-backup.tar.gz ./google-creds-backup.tar.gz

# Backup .env file
pct pull 101 /opt/mcp-servers/MCP_CREATOR/deployment/.env ./env-backup
```

## Performance Tips

### LXC Resource Allocation

For smooth operation:

**MCP Servers LXC:**
- Memory: 2GB minimum (4GB recommended if running all servers)
- CPU: 2 cores minimum
- Storage: 10GB

**Cloudflare Tunnel LXC:**
- Memory: 512MB
- CPU: 1 core
- Storage: 2GB

### Monitor Resource Usage

```bash
# On Proxmox host
pct exec 101 -- htop  # MCP servers
pct exec 102 -- htop  # Cloudflare tunnel
```

---

**Next Steps:**
1. Set up LXC containers
2. Get credentials (Google OAuth, Todoist token)
3. Deploy MCP servers
4. Configure Cloudflare Tunnel
5. Test from devices
6. Add Zero Trust authentication

You now have a complete, secure, remote MCP infrastructure!
