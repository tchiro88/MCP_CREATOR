# MCP Connectors - Self-Hosted Infrastructure Guide

## Overview

This repository contains comprehensive research and implementation guides for setting up your own Model Context Protocol (MCP) connector infrastructure. This enables you to expose MCP servers from your self-hosted environment to AI assistants across all platforms, similar to how Zapier and other integration platforms work.

## What is Model Context Protocol (MCP)?

The Model Context Protocol (MCP) is an **open standard, open-source framework** introduced by Anthropic in November 2024 to standardize how AI systems like large language models (LLMs) integrate with external tools, systems, and data sources.

### Key Facts

- **Latest Specification**: Version 2025-06-18 (Released June 18, 2025)
- **Industry Adoption**:
  - OpenAI officially adopted MCP in March 2025 (ChatGPT desktop, Agents SDK, Responses API)
  - Google DeepMind announced MCP support for Gemini models in April 2025
- **Official Specification**: https://modelcontextprotocol.io

## Architecture Components

MCP follows a **client-server architecture** with three main components:

### 1. MCP Clients
AI applications (like Claude Desktop, ChatGPT, etc.) that connect to MCP servers

### 2. MCP Servers
Standalone servers that expose specific functions and data to AI apps. Each server typically focuses on:
- A specific integration point (e.g., GitHub for repository access)
- A specific data source (e.g., PostgreSQL for database operations)
- Custom business logic and tools

### 3. Transport Layer
MCP formally specifies these standard transport mechanisms:
- **stdio**: Local, process-based communication
- **HTTP**: Remote access via HTTP requests
- **SSE (Server-Sent Events)**: Streaming data over HTTP

## Your Infrastructure Components

Based on your existing setup, you can leverage:

1. **Self-Hosted Server**: Host MCP servers locally
2. **Cloudflare Tunnel**: Securely expose local MCP servers without port forwarding
3. **Cloudflare Zero Trust**: Add authentication and access control
4. **n8n**: Create workflow automation bridges to MCP

## Repository Structure

```
MCP-connectors/
├── README.md                          # This file
├── research/                          # Detailed research findings
│   ├── mcp-protocol-overview.md      # MCP specification details
│   ├── transport-protocols.md        # stdio, HTTP, SSE details
│   └── security-oauth.md             # OAuth 2.1 authentication
├── architecture/                      # Architecture designs
│   ├── self-hosted-architecture.md   # Your infrastructure design
│   ├── cloudflare-tunnel-setup.md    # Cloudflare integration
│   └── n8n-integration.md            # n8n workflow bridges
├── deployment/                        # Deployment guides
│   ├── local-mcp-server.md           # Local server setup
│   ├── cloudflare-deployment.md      # Cloudflare Workers/Tunnel
│   └── docker-compose.yml            # Container orchestration
├── examples/                          # Example configurations
│   ├── simple-mcp-server/            # Basic MCP server example
│   ├── n8n-mcp-bridge/               # n8n integration example
│   └── authenticated-server/         # OAuth-enabled server
└── guides/                            # Step-by-step tutorials
    ├── quickstart.md                 # Get started quickly
    ├── cloudflare-tunnel-guide.md    # Detailed tunnel setup
    └── production-deployment.md      # Production best practices
```

## Quick Start Options

### Option 1: Use Existing n8n MCP Server
The fastest way to get started is using the existing n8n-MCP project:

```bash
npx n8n-mcp
```

### Option 2: Deploy to Cloudflare Workers
Deploy a remote MCP server to Cloudflare's edge network

### Option 3: Self-Hosted with Cloudflare Tunnel
Run MCP servers on your home server and expose them securely via Cloudflare Tunnel

### Option 4: Docker on VPS/Home Server
Deploy containerized MCP servers with full control

## Key Features of This Setup

- ✅ **Self-Hosted**: Full control over your data and infrastructure
- ✅ **Secure**: OAuth 2.1 authentication + Cloudflare Zero Trust
- ✅ **Scalable**: Can run multiple MCP servers for different purposes
- ✅ **Cross-Platform**: Accessible from any MCP client (Claude Desktop, ChatGPT, etc.)
- ✅ **No Port Forwarding**: Cloudflare Tunnel handles secure exposure
- ✅ **Integration Ready**: n8n for workflow automation bridges

## Latest Specification Updates (June 2025)

The 2025-06-18 specification introduced:

1. **Structured Tool Outputs**: Better formatting for tool responses
2. **OAuth-based Authorization**: MCP servers are now OAuth Resource Servers
3. **Elicitation**: Server-initiated user interactions
4. **Enhanced Security**: Resource Indicators to prevent token theft
5. **Improved Best Practices**: Security guidelines for production deployments

## Documentation Roadmap

This repository will document:

1. ✅ MCP protocol architecture and specifications
2. ✅ Self-hosted deployment strategies
3. ✅ Cloudflare Tunnel integration
4. ✅ n8n workflow automation bridges
5. 🔄 OAuth 2.1 authentication setup (in progress)
6. 🔄 Production deployment scripts (in progress)
7. 📋 Monitoring and logging solutions (planned)
8. 📋 Example MCP server implementations (planned)

## Next Steps

1. Read the [Architecture Guide](architecture/self-hosted-architecture.md)
2. Follow the [Quick Start Guide](guides/quickstart.md)
3. Review [Example Configurations](examples/)
4. Deploy your first MCP server!

## Resources

- **Official MCP Specification**: https://modelcontextprotocol.io
- **Cloudflare Agents Documentation**: https://developers.cloudflare.com/agents/
- **n8n MCP Project**: https://github.com/czlonkowski/n8n-mcp
- **GPT Tunnel (MCP over Cloudflare)**: https://gpt-tunnel.bgdn.dev

## Contributing

This is a research and implementation repository. Contributions, improvements, and real-world deployment experiences are welcome!

---

**Last Updated**: November 8, 2025
**MCP Specification Version**: 2025-06-18
