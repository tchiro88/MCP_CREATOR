# Cloudflare Tunnel Setup for MCP Servers

## Overview

Cloudflare Tunnel (formerly Argo Tunnel) allows you to securely expose your self-hosted MCP servers to the internet **without opening any inbound ports** on your firewall. This guide covers setup, configuration, and best practices.

## Why Cloudflare Tunnel?

### Traditional Setup (DON'T DO THIS)
```
Internet → Your Public IP:3001 → Router Port Forward → MCP Server
Problems:
- Exposes your home IP address
- Requires port forwarding (security risk)
- Vulnerable to DDoS attacks
- No built-in authentication
```

### Cloudflare Tunnel Setup (DO THIS)
```
Internet → Cloudflare Edge → Encrypted Tunnel → cloudflared → MCP Server
Benefits:
✅ No port forwarding required
✅ Hide your IP address
✅ DDoS protection from Cloudflare
✅ End-to-end encryption
✅ Integrate with Zero Trust authentication
✅ Free for basic usage
```

## Prerequisites

1. **Cloudflare Account**: Sign up at https://dash.cloudflare.com
2. **Domain Name**: Added to Cloudflare (can be free domain or purchased)
3. **Server Access**: SSH access to your home server
4. **cloudflared Binary**: Tunnel daemon (we'll install this)

## Installation

### Linux (Debian/Ubuntu)

```bash
# Download and install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

### Linux (RHEL/CentOS)

```bash
# Download and install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
sudo rpm -i cloudflared-linux-x86_64.rpm

# Verify
cloudflared --version
```

### macOS

```bash
# Using Homebrew
brew install cloudflare/cloudflare/cloudflared

# Verify
cloudflared --version
```

### Docker

```bash
# Pull the image
docker pull cloudflare/cloudflared:latest

# Verify
docker run cloudflare/cloudflared:latest --version
```

## Quick Start: Create Your First Tunnel

### Step 1: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will:
1. Open a browser window
2. Ask you to select a domain
3. Download a certificate to `~/.cloudflared/cert.pem`

### Step 2: Create a Tunnel

```bash
# Create a named tunnel
cloudflared tunnel create mcp-tunnel

# Output will show:
# Created tunnel mcp-tunnel with id: <tunnel-id>
# Credentials file: ~/.cloudflared/<tunnel-id>.json
```

**Important**: Save the tunnel ID and credentials file location!

### Step 3: Configure DNS

```bash
# Route a domain to your tunnel
cloudflared tunnel route dns mcp-tunnel mcp.yourdomain.com
```

This creates a CNAME record: `mcp.yourdomain.com → <tunnel-id>.cfargotunnel.com`

### Step 4: Create Configuration File

```bash
# Create config file
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

**Basic Configuration**:
```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/youruser/.cloudflared/<tunnel-id>.json

ingress:
  # Route all traffic for this domain to localhost:3001
  - hostname: mcp.yourdomain.com
    service: http://localhost:3001

  # Catch-all rule (required)
  - service: http_status:404
```

### Step 5: Test the Tunnel

```bash
# Start your MCP server first
node mcp-server.js --port 3001

# In another terminal, run the tunnel
cloudflared tunnel run mcp-tunnel
```

Visit `https://mcp.yourdomain.com` - you should see your MCP server!

### Step 6: Run as a Service

```bash
# Install the tunnel as a system service
sudo cloudflared service install

# Start the service
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

## Advanced Configuration

### Multiple MCP Servers

```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/youruser/.cloudflared/<tunnel-id>.json

ingress:
  # GitHub MCP Server
  - hostname: mcp-github.yourdomain.com
    service: http://localhost:3001

  # Database MCP Server
  - hostname: mcp-db.yourdomain.com
    service: http://localhost:3002

  # n8n MCP Gateway
  - hostname: mcp-n8n.yourdomain.com
    service: http://localhost:3003

  # n8n UI (optional)
  - hostname: n8n.yourdomain.com
    service: http://localhost:5678

  # Catch-all
  - service: http_status:404
```

Then route each domain:
```bash
cloudflared tunnel route dns mcp-tunnel mcp-github.yourdomain.com
cloudflared tunnel route dns mcp-tunnel mcp-db.yourdomain.com
cloudflared tunnel route dns mcp-tunnel mcp-n8n.yourdomain.com
cloudflared tunnel route dns mcp-tunnel n8n.yourdomain.com
```

### Path-Based Routing

```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/youruser/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: mcp.yourdomain.com
    path: ^/github(/.*)?$
    service: http://localhost:3001

  - hostname: mcp.yourdomain.com
    path: ^/database(/.*)?$
    service: http://localhost:3002

  - hostname: mcp.yourdomain.com
    path: ^/n8n(/.*)?$
    service: http://localhost:3003

  - hostname: mcp.yourdomain.com
    service: http://localhost:8080  # Default service

  - service: http_status:404
```

### WebSocket Support

```yaml
ingress:
  - hostname: mcp-ws.yourdomain.com
    service: http://localhost:3001
    originRequest:
      noTLSVerify: false
      connectTimeout: 30s
      # Enable WebSocket
      httpHostHeader: mcp-ws.yourdomain.com
```

**Note**: MCP with SSE (Server-Sent Events) requires HTTP/2, which is supported by default.

### Custom Headers

```yaml
ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:3001
    originRequest:
      # Add custom headers
      httpHostHeader: mcp.yourdomain.com
      caPool: /path/to/ca.pem
      noTLSVerify: false
```

## Cloudflare Zero Trust Integration

### Enable Zero Trust Authentication

1. **Go to Cloudflare Zero Trust Dashboard**:
   - https://one.dash.cloudflare.com/

2. **Create an Application**:
   - Access → Applications → Add an application
   - Select: Self-hosted
   - Name: MCP Server
   - Session Duration: 24 hours
   - Application domain: mcp.yourdomain.com

3. **Configure Authentication**:
   - Add an identity provider:
     - One-time PIN
     - Google
     - GitHub
     - Azure AD
     - Okta
     - etc.

4. **Create Access Policies**:

**Example: Email-Based Access**
```
Policy Name: Allow Company Emails
Action: Allow
Include:
  - Emails ending in: @yourcompany.com
```

**Example: Country-Based Restriction**
```
Policy Name: Geo Restriction
Action: Block
Exclude:
  - Country: United States, Canada, UK
```

**Example: Multi-Factor Authentication**
```
Policy Name: MFA Required
Action: Allow
Require:
  - Emails ending in: @yourcompany.com
AND
  - Authentication Method: Google with 2FA
```

5. **Advanced Options**:
   - **Purpose Justification**: Require users to explain why they're accessing
   - **Temporary Authentication**: Time-limited access
   - **Device Posture**: Require specific device configurations

### Access Policy Examples for MCP

**Production MCP Server** (Strict):
```
Application: mcp-prod.yourdomain.com
Policies:
  1. Allow:
     - Email: your-email@company.com
     - Require: GitHub authentication with 2FA
     - Country: Specific countries only
     - Purpose: Required with approval

  2. Block:
     - Everyone else
```

**Development MCP Server** (Relaxed):
```
Application: mcp-dev.yourdomain.com
Policies:
  1. Allow:
     - Emails ending in: @yourcompany.com
     - Session: 24 hours

  2. Block:
     - Everyone else
```

## Security Best Practices

### 1. Don't Use Quick Tunnels for Production

**Quick Tunnel** (for testing only):
```bash
cloudflared tunnel --url http://localhost:3001
# Generates random URL like: https://random-string.trycloudflare.com
```

**Issues**:
- Random, non-persistent URLs
- No access control
- No custom domain
- **Does NOT support SSE** (important for MCP!)
- Anyone with the URL can access

### 2. Always Use Named Tunnels

```bash
# Create persistent tunnel
cloudflared tunnel create production-mcp
```

Benefits:
- Persistent tunnel ID
- Custom domains
- Full configuration control
- SSE support
- Access control via Zero Trust

### 3. Enable HTTPS Only

Cloudflare automatically provides HTTPS, but ensure your origin (MCP server) also supports TLS if needed:

```yaml
ingress:
  - hostname: mcp.yourdomain.com
    service: https://localhost:3001  # Note: https://
    originRequest:
      noTLSVerify: false  # Verify TLS certificate
      caPool: /path/to/ca.pem  # Custom CA if self-signed
```

### 4. Implement Rate Limiting

Use Cloudflare Rate Limiting rules:

1. Go to: Security → WAF → Rate limiting rules
2. Create rule:
   - Name: MCP Rate Limit
   - If incoming requests match:
     - Hostname equals `mcp.yourdomain.com`
   - Then:
     - Block for 10 minutes
     - If threshold is 100 requests per 1 minute

### 5. Monitor Access Logs

Enable Cloudflare Access Logs:

1. Zero Trust → Logs → Access
2. View authentication attempts
3. Set up alerts for:
   - Failed authentication attempts
   - Access from new countries
   - Unusual access patterns

## Docker Deployment

### Docker Compose Example

```yaml
version: '3.8'

services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run
    volumes:
      - ./cloudflared-config:/etc/cloudflared
    environment:
      - TUNNEL_TOKEN=${TUNNEL_TOKEN}
    restart: unless-stopped
    networks:
      - mcp-network

  mcp-server:
    image: your-mcp-server:latest
    ports:
      - "3001:3000"
    networks:
      - mcp-network
    restart: unless-stopped

networks:
  mcp-network:
    driver: bridge
```

### Get Tunnel Token

Instead of using `config.yml`, you can use a token:

```bash
# Create tunnel and get token
cloudflared tunnel create mcp-tunnel

# Generate token
cloudflared tunnel token mcp-tunnel
# Output: eyJhIjoiNjk...long-token-string...
```

Use in Docker Compose:
```yaml
environment:
  - TUNNEL_TOKEN=eyJhIjoiNjk...
```

## Troubleshooting

### Issue: Tunnel Not Starting

**Check logs**:
```bash
# If running as service
sudo journalctl -u cloudflared -f

# If running manually
cloudflared tunnel --loglevel debug run mcp-tunnel
```

**Common causes**:
- Incorrect tunnel ID in config
- Credentials file not found
- MCP server not running
- Port already in use

### Issue: 502 Bad Gateway

**Causes**:
- MCP server not running on specified port
- Firewall blocking localhost connections
- MCP server crashed

**Solution**:
```bash
# Check if MCP server is running
curl http://localhost:3001

# Check firewall
sudo iptables -L

# Restart MCP server
systemctl restart mcp-server
```

### Issue: SSL/TLS Errors

**Cause**: MCP server using self-signed certificate

**Solution**:
```yaml
ingress:
  - hostname: mcp.yourdomain.com
    service: https://localhost:3001
    originRequest:
      noTLSVerify: true  # Allow self-signed certs
```

Or provide CA certificate:
```yaml
originRequest:
  caPool: /path/to/self-signed-ca.pem
```

### Issue: SSE Not Working

**Note**: Quick Tunnels (trycloudflare.com) do NOT support SSE!

**Solution**: Use named tunnel with proper configuration:
```yaml
ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:3001
    originRequest:
      httpHostHeader: mcp.yourdomain.com
      # Ensure HTTP/2 is enabled (default)
```

## Monitoring & Maintenance

### Health Checks

Add health check endpoint to your MCP server:

```javascript
// Express.js example
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: Date.now() });
});
```

Configure monitoring:
```yaml
ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:3001
    originRequest:
      # Health check configuration
      httpHostHeader: mcp.yourdomain.com
```

### Metrics

View tunnel metrics:
1. Cloudflare Dashboard → Traffic → Analytics
2. Zero Trust Dashboard → Analytics

Key metrics:
- Requests per second
- Bandwidth usage
- Error rates (4xx, 5xx)
- Authentication success/failure rates

### Backup Configuration

```bash
# Backup tunnel credentials
cp ~/.cloudflared/<tunnel-id>.json ~/backups/

# Backup configuration
cp ~/.cloudflared/config.yml ~/backups/

# Store in Git
git add backups/
git commit -m "Backup Cloudflare Tunnel config"
```

## Cost Considerations

### Free Tier (Cloudflare Tunnel)
- ✅ Unlimited bandwidth
- ✅ Unlimited tunnels
- ✅ DDoS protection
- ✅ SSL/TLS certificates
- ✅ Basic analytics

### Zero Trust Pricing
- **Free**: Up to 50 users
- **Standard**: $7/user/month (additional users)
- **Enterprise**: Custom pricing

**For personal/small team use**: Completely free!

## Advanced: Tunnel Replicas

For high availability, run multiple tunnel instances:

```yaml
# Server 1
tunnel: mcp-tunnel-1
credentials-file: /path/to/tunnel-1.json
ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:3001
  - service: http_status:404

# Server 2
tunnel: mcp-tunnel-2
credentials-file: /path/to/tunnel-2.json
ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:3001
  - service: http_status:404
```

Cloudflare automatically load balances between active tunnels.

## Next Steps

1. Review [OAuth 2.1 Setup Guide](../research/security-oauth.md)
2. Deploy [Example MCP Server](../examples/simple-mcp-server/)
3. Configure [n8n Integration](n8n-integration.md)
4. Set up [Monitoring & Alerts](../guides/production-deployment.md)

## Resources

- **Cloudflare Tunnel Docs**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- **Zero Trust Docs**: https://developers.cloudflare.com/cloudflare-one/
- **MCP Remote Servers**: https://developers.cloudflare.com/agents/guides/remote-mcp-server/
- **GPT Tunnel**: https://gpt-tunnel.bgdn.dev

---

**Document Version**: 1.0
**Last Updated**: November 8, 2025
