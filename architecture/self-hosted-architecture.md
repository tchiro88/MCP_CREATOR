# Self-Hosted MCP Architecture

## Overview

This document describes the architecture for running your own MCP connector infrastructure using self-hosted servers, Cloudflare Tunnel, and optional n8n integration.

## Architecture Goals

1. **Full Control**: Host MCP servers on your own infrastructure
2. **Secure Access**: Expose servers without port forwarding or public IPs
3. **Cross-Platform**: Accessible from any MCP client (Claude, ChatGPT, etc.)
4. **Scalable**: Support multiple MCP servers for different purposes
5. **Integrated**: Leverage n8n for workflow automation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Internet / Cloud                            │
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │ Claude       │      │   ChatGPT    │      │ Other MCP    │  │
│  │ Desktop      │      │   Desktop    │      │ Clients      │  │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘  │
│         │                     │                     │           │
│         └─────────────────────┼─────────────────────┘           │
│                               │                                 │
│                  ┌────────────▼──────────────┐                  │
│                  │  Cloudflare Edge Network  │                  │
│                  │  ┌─────────────────────┐  │                  │
│                  │  │  Zero Trust Access  │  │                  │
│                  │  │   Control Layer     │  │                  │
│                  │  └─────────────────────┘  │                  │
│                  └────────────┬──────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                    Cloudflare Tunnel
                    (Encrypted, No Inbound Ports)
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   Your Home/Private Network                      │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Cloudflare Tunnel Daemon                      │  │
│  │              (cloudflared running locally)                 │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                       │
│          ┌───────────────┼───────────────┐                      │
│          │               │               │                      │
│  ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐               │
│  │ MCP Server 1 │ │ MCP Server│ │  n8n MCP   │               │
│  │  (GitHub)    │ │     2      │ │  Gateway   │               │
│  │              │ │ (Database) │ │            │               │
│  │ Port: 3001   │ │ Port: 3002 │ │ Port: 3003 │               │
│  └──────────────┘ └────────────┘ └─────┬──────┘               │
│                                         │                        │
│                          ┌──────────────▼──────────────┐        │
│                          │      n8n Instance           │        │
│                          │  (Workflow Automation)      │        │
│                          └─────────────────────────────┘        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Local Resources                              │  │
│  │  • Databases (PostgreSQL, MySQL, etc.)                   │  │
│  │  • File Systems                                          │  │
│  │  • Internal APIs                                         │  │
│  │  • Docker Containers                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Cloudflare Tunnel

**Purpose**: Securely expose local MCP servers without port forwarding

**How It Works**:
- `cloudflared` daemon runs on your local network
- Establishes **outbound** encrypted connection to Cloudflare
- No inbound ports need to be opened on your firewall
- Cloudflare routes requests through the tunnel to your local servers

**Configuration Example**:
```yaml
# config.yml for cloudflared
tunnel: your-tunnel-id
credentials-file: /path/to/credentials.json

ingress:
  # MCP Server 1: GitHub Integration
  - hostname: mcp-github.yourdomain.com
    service: http://localhost:3001

  # MCP Server 2: Database Access
  - hostname: mcp-db.yourdomain.com
    service: http://localhost:3002

  # n8n MCP Gateway
  - hostname: mcp-n8n.yourdomain.com
    service: http://localhost:3003

  # Catch-all
  - service: http_status:404
```

**Security Features**:
- End-to-end encryption
- DDoS protection from Cloudflare
- No exposed IP addresses
- No open ports on your network

### 2. Cloudflare Zero Trust

**Purpose**: Add authentication and access control layer

**Features**:
- **Identity Verification**: Require email, Google, GitHub, etc. authentication
- **Access Policies**: Define who can access which MCP servers
- **Audit Logs**: Track all access attempts
- **Session Management**: Control session duration and reauthentication

**Example Access Policy**:
```
Application: mcp-github.yourdomain.com
Policy:
  - Allow: Emails ending in @yourcompany.com
  - Require: GitHub authentication
  - Session Duration: 24 hours
  - Country: Allowed countries list
```

### 3. MCP Servers (Self-Hosted)

**Deployment Options**:

#### Option A: Docker Containers
```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-github:
    image: your-mcp-github-server:latest
    ports:
      - "3001:3000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - MCP_SERVER_NAME=github-mcp
    restart: unless-stopped

  mcp-database:
    image: your-mcp-database-server:latest
    ports:
      - "3002:3000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - MCP_SERVER_NAME=database-mcp
    restart: unless-stopped

  mcp-n8n-gateway:
    image: ghcr.io/czlonkowski/n8n-mcp:latest
    ports:
      - "3003:3000"
    environment:
      - N8N_API_URL=${N8N_API_URL}
      - N8N_API_KEY=${N8N_API_KEY}
    restart: unless-stopped
```

#### Option B: Native Node.js Processes
```bash
# Run each MCP server as a separate process
pm2 start mcp-github.js --name mcp-github
pm2 start mcp-database.js --name mcp-database
pm2 start mcp-n8n.js --name mcp-n8n
```

#### Option C: Docker Compose with Traefik
```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  mcp-github:
    image: your-mcp-github-server:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-github.rule=Host(`localhost`) && PathPrefix(`/github`)"
      - "traefik.http.services.mcp-github.loadbalancer.server.port=3000"
```

### 4. n8n Integration Layer

**Purpose**: Bridge between n8n workflows and MCP protocol

**Architecture**:
```
MCP Client → MCP Gateway → n8n API → n8n Workflows → Actions
```

**Use Cases**:
1. **Workflow Creation**: AI creates n8n workflows via MCP
2. **Workflow Execution**: AI triggers workflows with parameters
3. **Workflow Monitoring**: AI checks workflow status and results
4. **Data Transformation**: AI uses n8n to transform data between systems

**Example Flow**:
```
User → Claude: "Create a workflow to sync GitHub issues to Notion"
Claude → n8n MCP Server: create_workflow(...)
n8n MCP Server → n8n API: POST /workflows
n8n: Creates workflow with GitHub + Notion nodes
n8n → n8n MCP Server: {workflow_id: 123, url: "..."}
n8n MCP Server → Claude: Success response
Claude → User: "Workflow created at [URL]"
```

## Data Flow

### 1. Remote MCP Request Flow

```
┌─────────────┐
│ MCP Client  │ (e.g., Claude Desktop)
└──────┬──────┘
       │ 1. HTTPS Request
       │    GET /mcp/v1/tools/list
       │    Authorization: Bearer <token>
       ▼
┌──────────────────┐
│ Cloudflare Edge  │
└──────┬───────────┘
       │ 2. Zero Trust Check
       │    - Verify user identity
       │    - Check access policies
       │    - Validate session
       ▼
┌──────────────────┐
│ Cloudflare       │
│ Tunnel           │
└──────┬───────────┘
       │ 3. Encrypted tunnel to your network
       ▼
┌──────────────────┐
│ cloudflared      │ (running on your server)
└──────┬───────────┘
       │ 4. HTTP to localhost:3001
       ▼
┌──────────────────┐
│ MCP Server       │
└──────┬───────────┘
       │ 5. Process request
       │    - Validate OAuth token
       │    - Execute tool/resource request
       │    - Format response
       ▼
┌──────────────────┐
│ Response         │
└──────────────────┘
       │
       │ 6. Return through tunnel
       ▼
Back to MCP Client
```

### 2. n8n Workflow Request Flow

```
MCP Client
    │
    ▼
n8n MCP Gateway (Port 3003)
    │
    ├─→ n8n API: Create Workflow
    │       │
    │       └─→ n8n saves workflow definition
    │
    ├─→ n8n API: Execute Workflow
    │       │
    │       └─→ n8n executes nodes → External APIs
    │
    └─→ n8n API: Get Execution Results
            │
            └─→ Return execution data
```

## Network Architecture

### Ports and Services

| Service | Internal Port | External URL | Purpose |
|---------|--------------|--------------|---------|
| MCP Server 1 (GitHub) | 3001 | mcp-github.yourdomain.com | GitHub integration |
| MCP Server 2 (Database) | 3002 | mcp-db.yourdomain.com | Database access |
| n8n MCP Gateway | 3003 | mcp-n8n.yourdomain.com | n8n workflow bridge |
| n8n Instance | 5678 | n8n.yourdomain.com | n8n UI (optional) |
| Cloudflare Tunnel | - | - | Tunnel daemon |

### Firewall Rules

**Inbound Rules**: NONE (that's the point!)

**Outbound Rules**:
- Allow: HTTPS (443) to Cloudflare
- Allow: HTTP/HTTPS to external APIs (GitHub, etc.)
- Allow: Database connections (if external)

### DNS Configuration

```
# Cloudflare DNS
mcp-github.yourdomain.com  → CNAME → your-tunnel-id.cfargotunnel.com
mcp-db.yourdomain.com      → CNAME → your-tunnel-id.cfargotunnel.com
mcp-n8n.yourdomain.com     → CNAME → your-tunnel-id.cfargotunnel.com
```

## Security Architecture

### Multi-Layer Security

#### Layer 1: Cloudflare Zero Trust
- Identity verification
- Access policies
- Country restrictions
- Device posture checks

#### Layer 2: OAuth 2.1 (MCP Server)
- Token-based authentication
- Resource indicators (RFC 8707)
- Token expiration and refresh
- Scope-based permissions

#### Layer 3: Application-Level Security
- Input validation
- Rate limiting
- Audit logging
- Error handling without information disclosure

### Authentication Flow

```
1. User opens MCP Client (e.g., Claude Desktop)
2. Client detects remote MCP server URL
3. Client initiates OAuth flow:
   a. Redirect to authorization server
   b. User authenticates
   c. Authorization server returns code
   d. Client exchanges code for token
4. Client includes token in MCP requests
5. Cloudflare Zero Trust validates user session
6. Cloudflare Tunnel forwards request
7. MCP Server validates OAuth token
8. MCP Server processes request
```

## Scalability Considerations

### Horizontal Scaling

**Option 1: Multiple Tunnel Instances**
```
Load Balancer (Cloudflare)
    │
    ├─→ Tunnel 1 → MCP Servers (Server 1)
    ├─→ Tunnel 2 → MCP Servers (Server 2)
    └─→ Tunnel 3 → MCP Servers (Server 3)
```

**Option 2: Docker Swarm/Kubernetes**
```yaml
# Deploy MCP servers as replicas
services:
  mcp-github:
    image: your-mcp-github-server:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement caching (Redis, Memcached)
- Use connection pooling

### Caching Strategy

```
┌──────────────┐
│ MCP Client   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ MCP Server   │
└──────┬───────┘
       │
       ├─→ Check Redis cache
       │   └─→ Cache hit? Return
       │
       └─→ Cache miss
           └─→ Query backend
               └─→ Store in cache
                   └─→ Return
```

## Monitoring & Observability

### Key Metrics to Track

1. **Request Metrics**:
   - Requests per second
   - Response times (p50, p95, p99)
   - Error rates

2. **System Metrics**:
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network throughput

3. **Business Metrics**:
   - Tool usage frequency
   - Active users
   - Authentication success/failure rates

### Logging Architecture

```
MCP Servers
    │
    └─→ Logs → Loki/Elasticsearch
                   │
                   └─→ Grafana Dashboard
                   └─→ Alert Manager
```

### Recommended Tools

- **Metrics**: Prometheus + Grafana
- **Logs**: Loki or Elasticsearch + Kibana
- **Tracing**: Jaeger or Zipkin
- **Uptime**: UptimeRobot or Pingdom
- **Errors**: Sentry

## Cost Analysis

### Infrastructure Costs

| Component | Cost | Notes |
|-----------|------|-------|
| Cloudflare Tunnel | Free | Zero Trust has paid tiers |
| Cloudflare Zero Trust | $0-7/user/month | First 50 users free |
| Self-Hosted Server | $0-50/month | Depends on hardware |
| Domain Name | $10-15/year | Required for tunnel |
| n8n Self-Hosted | Free | Open source |

**Total Estimated Monthly Cost**: $0-50/month (excluding domain)

Compare to:
- Zapier: $29.99-$103.50/month
- Make (Integromat): $9-$29/month
- Custom VPS: $5-20/month

## Deployment Models

### Model 1: Single Server (Recommended for Start)
- All MCP servers on one machine
- Single Cloudflare Tunnel
- Simplest to manage

### Model 2: Distributed Servers
- MCP servers on different machines
- Multiple Cloudflare Tunnels
- Better fault tolerance

### Model 3: Hybrid Cloud
- Some MCP servers self-hosted
- Some on cloud providers (Cloudflare Workers, Google Cloud Run)
- Balance of control and convenience

## Disaster Recovery

### Backup Strategy

1. **MCP Server Configurations**: Git repository
2. **n8n Workflows**: Export regularly, store in Git
3. **Databases**: Regular backups (daily)
4. **Cloudflare Tunnel Config**: Version controlled

### Recovery Procedures

```bash
# 1. Restore Cloudflare Tunnel
cloudflared tunnel create backup-tunnel
cloudflared tunnel route dns backup-tunnel mcp.yourdomain.com

# 2. Restore MCP servers
docker-compose up -d

# 3. Restore n8n workflows
n8n import:workflow --input=./backups/workflows.json

# 4. Verify connectivity
curl https://mcp-github.yourdomain.com/health
```

## Next Steps

1. Review [Cloudflare Tunnel Setup Guide](../deployment/cloudflare-deployment.md)
2. Set up [OAuth 2.1 Authentication](../research/security-oauth.md)
3. Deploy [Example MCP Server](../examples/simple-mcp-server/)
4. Configure [n8n Integration](n8n-integration.md)

---

**Document Version**: 1.0
**Last Updated**: November 8, 2025
