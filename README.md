# MCP_CREATOR

**Self-hosted MCP (Model Context Protocol) connector infrastructure** - Access Gmail, GitHub, Todoist, Slack, Notion, Home Assistant, and iCloud from Claude on any device (iPhone, laptop, desktop).

## 🚀 Quick Start

Choose your path:

| I want to... | Guide | Time |
|-------------|-------|------|
| **Deploy everything on Proxmox with all 8 connectors** | [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) | 1-2 hours |
| **Quick minimal setup (2-3 connectors)** | [QUICKSTART-MINIMAL.md](QUICKSTART-MINIMAL.md) | 30-45 min |
| **Get API credentials for all services** | [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md) | Reference |

## 📦 What's Included

### 8 Production-Ready MCP Connectors + Cross-Service Integrator

| Connector | Services | Status | Documentation |
|-----------|----------|--------|---------------|
| **GitHub** | Repos, Issues, PRs, Actions | ✅ Ready | [mcp/github/README.md](mcp/github/README.md) |
| **Google** | Gmail, Drive, Calendar, Photos | ✅ Ready | [mcp/google/README.md](mcp/google/README.md) |
| **Todoist** | Tasks, Projects, Labels | ✅ Ready | [mcp/todoist/README.md](mcp/todoist/README.md) |
| **Home Assistant** | Smart Home Control | ✅ Ready | [mcp/homeassistant/README.md](mcp/homeassistant/README.md) |
| **Notion** | Databases, Pages, Blocks | ✅ Ready | [mcp/notion/README.md](mcp/notion/README.md) |
| **Slack** | Messages, Channels, Files | ✅ Ready | [mcp/slack/README.md](mcp/slack/README.md) |
| **iCloud** | Mail, Calendar, Contacts, Drive | ✅ Ready | [mcp/icloud/README.md](mcp/icloud/README.md) |
| **Outlook** | Email, Calendar (Read-Only) + Priority AI | ✅ Ready | [mcp/outlook/README.md](mcp/outlook/README.md) |
| **Integrator** | Cross-Service Intelligence (Meta-MCP) | ✅ Ready | [mcp/integrator/README.md](mcp/integrator/README.md) |

### Key Features

✅ **Remote Access** - Use from iPhone, laptop, any device with Claude
✅ **Secure** - No port forwarding needed (Cloudflare Tunnel)
✅ **Self-Hosted** - Full control, runs on Proxmox/VPS/home server
✅ **Zero Trust** - Optional Cloudflare authentication layer
✅ **Docker-Based** - Easy deployment and updates
✅ **Production-Ready** - Complete with monitoring and logging

## 📖 Documentation

### Getting Started
- **[SETUP.md](SETUP.md)** - Complete setup guide for all MCP services
- **[CLOUDFLARE-TUNNEL-SETUP.md](CLOUDFLARE-TUNNEL-SETUP.md)** - Remote access setup for any device (iPhone, laptop, etc.)
- **[TUNNEL-SETUP-COMMANDS.md](TUNNEL-SETUP-COMMANDS.md)** - Quick command reference for SSH/terminal setup
- **[CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md)** - How to obtain credentials for all services
- **[CLAUDE-DESKTOP-SETUP.md](CLAUDE-DESKTOP-SETUP.md)** - Claude Desktop configuration guide

### Architecture & Research
- **[architecture/self-hosted-architecture.md](architecture/self-hosted-architecture.md)** - System design and architecture
- **[architecture/cloudflare-tunnel-setup.md](architecture/cloudflare-tunnel-setup.md)** - Cloudflare Tunnel configuration
- **[research/mcp-protocol-overview.md](research/mcp-protocol-overview.md)** - MCP protocol specification
- **[research/security-oauth.md](research/security-oauth.md)** - OAuth 2.1 security implementation

### Deployment Resources
- **[deployment/DEPLOYMENT-COMPLETE.md](deployment/DEPLOYMENT-COMPLETE.md)** - Production deployment reference
- **[deployment/PROXMOX-SETUP.md](deployment/PROXMOX-SETUP.md)** - Proxmox-specific configuration

## 🎯 Architecture Overview

```
┌─────────────────┐
│  Your Devices   │  ← iPhone, Laptop, Desktop
│ (Claude Apps)   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Cloudflare     │  ← Zero Trust + Tunnel
│  Edge Network   │
└────────┬────────┘
         │ Encrypted Tunnel
         ▼
┌─────────────────┐
│ Proxmox Server  │
│   (LXC/Docker)  │  ← Your self-hosted infrastructure
│                 │
│  7 MCP Servers  │  ← GitHub, Google, Todoist, etc.
└─────────────────┘
```

## 🔧 What You Need

**Hardware:**
- Proxmox server, VPS, or any Linux machine with Docker
- 4GB RAM minimum (2GB for minimal setup)
- 20GB disk space

**Services:**
- Domain name (pointed to Cloudflare)
- Cloudflare account (free tier works)
- API credentials for services you want to use

**Total Cost:** ~$10-15/year (just domain if self-hosting)

## 📱 Use Cases

Once deployed, ask Claude to:

**Gmail:**
- "Check my unread emails"
- "Search for emails from john@example.com about the project"
- "Send an email to..."

**GitHub:**
- "List my repositories"
- "Create an issue in my-repo"
- "Show open PRs"

**Todoist:**
- "What tasks are due today?"
- "Create a new task: Deploy MCP servers"
- "Complete the task 'Setup credentials'"

**Home Assistant:**
- "Turn on the living room lights"
- "What's the temperature in the bedroom?"
- "Set thermostat to 72 degrees"

**Notion:**
- "List my databases"
- "Create a new page in my Notes database"
- "Query my Tasks database"

**Slack:**
- "Show recent messages in #general"
- "Send a message to #team"
- "Search for 'deployment' in Slack"

**iCloud:**
- "Check my iCloud calendar for today"
- "List my iCloud reminders"
- "Show my iCloud contacts"

**Outlook:**
- "Check my Outlook unread emails"
- "Build my priority action list for today"
- "Give me my daily briefing"
- "What's on my Outlook calendar?"

**Integrator (Cross-Service):**
- "Show me ALL my unread messages" (Outlook + Gmail + Slack)
- "Give me a comprehensive briefing" (all services)
- "Search everywhere for 'project alpha'"
- "Check health of all my MCP services"

## 🛡️ Security

All credentials are:
- ✅ Gitignored (never committed)
- ✅ Encrypted in transit (Cloudflare Tunnel)
- ✅ Restricted permissions (chmod 600)
- ✅ Optional Zero Trust authentication

See [DEPLOYMENT-GUIDE.md - Security Setup](DEPLOYMENT-GUIDE.md#security-setup)

## 🤝 Contributing

Contributions welcome! To add a new MCP connector:

1. Create `mcp/yourservice/` directory
2. Implement using MCP SDK
3. Add to `docker-compose.minimal.yml`
4. Document in `mcp/yourservice/README.md`
5. Submit PR

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Built with:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) by Anthropic
- [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/)
- Docker & Docker Compose
- Python 3.11+

---

**Need Help?**
- 📖 Start with [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)
- 🔑 Credential issues? See [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md)
- 🐛 Found a bug? [Open an issue](https://github.com/tchiro88/MCP_CREATOR/issues)

**Last Updated:** 2025-11-09
