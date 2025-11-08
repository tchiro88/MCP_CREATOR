# Model Context Protocol (MCP) - Protocol Overview

## Introduction

Model Context Protocol (MCP) is an open standard framework introduced by Anthropic in November 2024 that standardizes how artificial intelligence systems (especially Large Language Models) integrate with external tools, systems, and data sources.

## Timeline & Adoption

### November 2024
- **Initial Release**: Anthropic introduces MCP as an open-source standard
- First specification published at modelcontextprotocol.io

### March 2025
- **OpenAI Adoption**: OpenAI officially adopts MCP across:
  - ChatGPT desktop app
  - OpenAI's Agents SDK
  - Responses API

### April 2025
- **Google DeepMind Adoption**: Demis Hassabis confirms MCP support in:
  - Upcoming Gemini models
  - Related Google AI infrastructure

### June 18, 2025
- **Latest Specification**: Version 2025-06-18 released with major updates

## Core Architecture

MCP follows a **client-server architecture** to connect AI models with external context.

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   MCP Client    │ ◄─────► │   Transport     │ ◄─────► │   MCP Server    │
│  (AI Assistant) │         │  Layer (stdio/  │         │  (Data/Tools)   │
│                 │         │   HTTP/SSE)     │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### 1. MCP Clients

**Definition**: AI applications that connect to MCP servers

**Examples**:
- Claude Desktop
- ChatGPT desktop app
- Cursor IDE
- Windsurf
- Custom AI applications

**Responsibilities**:
- Discover available MCP servers
- Establish connections via transport protocols
- Send requests for tools, resources, and prompts
- Handle authentication (OAuth 2.1)
- Present results to users

### 2. MCP Servers

**Definition**: Services that expose specific functions, data, and capabilities to AI applications

**Characteristics**:
- Each server is typically focused on a specific integration
- Stateless or stateful depending on implementation
- Can expose multiple tools, resources, and prompts
- Must implement security best practices

**Examples**:
- GitHub MCP Server: Repository access, PR management, issue tracking
- PostgreSQL MCP Server: Database queries, schema inspection
- Filesystem MCP Server: File operations
- Custom business logic servers

**Server Components**:
```json
{
  "tools": ["create_issue", "search_repos", "get_pull_request"],
  "resources": ["repo://owner/name", "issue://123"],
  "prompts": ["review_pr", "generate_docs"]
}
```

### 3. Transport Layer

MCP formally specifies these standard transport mechanisms:

#### stdio (Standard Input/Output)
- **Use Case**: Local, process-based communication
- **How It Works**: MCP server runs as a subprocess, communicates via stdin/stdout
- **Advantages**: Simple, fast, secure for local use
- **Disadvantages**: Limited to local machine

```bash
# Example: Running MCP server via stdio
node mcp-server.js
```

#### HTTP (with optional SSE)
- **Use Case**: Remote access to MCP servers
- **How It Works**: RESTful HTTP requests, optional Server-Sent Events for streaming
- **Advantages**: Works across networks, standard protocol
- **Disadvantages**: Requires authentication, more complex setup

**HTTP Endpoints**:
```
POST /mcp/v1/tools/call
GET  /mcp/v1/resources/{id}
POST /mcp/v1/prompts/get
```

#### SSE (Server-Sent Events)
- **Use Case**: Streaming data from MCP server to client
- **How It Works**: One-way event stream over HTTP
- **Advantages**: Real-time updates, efficient for streaming
- **Note**: Quick Tunnels (TryCloudflare) do NOT support SSE

## Protocol Features

### Tools
Functions that MCP servers expose to AI assistants

**Example Tool Definition**:
```json
{
  "name": "create_github_issue",
  "description": "Creates a new GitHub issue",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "body": {"type": "string"},
      "labels": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["title"]
  }
}
```

### Resources
Data sources that MCP servers can provide to AI assistants

**Example Resource**:
```json
{
  "uri": "repo://anthropics/anthropic-sdk-python",
  "name": "Anthropic Python SDK Repository",
  "mimeType": "application/json"
}
```

### Prompts
Reusable prompt templates that MCP servers can offer

**Example Prompt**:
```json
{
  "name": "review_code",
  "description": "Review code changes for best practices",
  "arguments": [
    {"name": "diff", "description": "The code diff to review"}
  ]
}
```

## Authentication & Security

### OAuth 2.1 (June 2025 Specification)

**Key Requirements**:
- MCP servers are now officially classified as **OAuth Resource Servers**
- Clients must implement **Resource Indicators** (RFC 8707) to prevent malicious servers from obtaining access tokens
- Authorization headers must be validated
- Token introspection should be implemented

**Security Best Practices**:
1. ✅ Always use OAuth 2.1 for remote MCP servers
2. ✅ Implement proper token validation
3. ✅ Use HTTPS for all remote connections
4. ✅ Validate all inputs (prevent injection attacks)
5. ✅ Implement rate limiting
6. ✅ Log all authentication attempts
7. ⚠️ **WARNING**: If you don't enforce authentication, anyone on the public internet can access your MCP server

### Zero Trust Architecture

For self-hosted deployments, combine:
- **Cloudflare Tunnel**: Encrypted tunnel (no inbound ports)
- **Cloudflare Zero Trust**: Restrict access to authenticated users
- **OAuth 2.1**: Application-level authentication

## June 2025 Specification Updates

### 1. Structured Tool Outputs
Better formatting and typing for tool responses

**Before**:
```json
{"result": "Operation completed"}
```

**After**:
```json
{
  "result": {
    "type": "success",
    "data": {"issueId": 123, "url": "https://..."},
    "metadata": {"executionTime": "120ms"}
  }
}
```

### 2. OAuth-based Authorization
- MCP servers are now OAuth Resource Servers
- Clients must implement Resource Indicators (RFC 8707)
- Prevents malicious servers from stealing access tokens

### 3. Elicitation
Server-initiated user interactions

**Use Cases**:
- Request additional information from user
- Ask for confirmation before destructive operations
- Multi-step workflows requiring user input

**Example Flow**:
```
Server → Client: "Please confirm deletion of repository X"
Client → User: Shows confirmation dialog
User → Client: Confirms
Client → Server: Proceeds with operation
```

### 4. Enhanced Security Best Practices
Official guidelines for:
- Input validation
- Rate limiting
- Token management
- Error handling
- Audit logging

## Protocol Evolution

### Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.0 | Nov 2024 | Initial release, stdio transport |
| 2024-12 | Dec 2024 | HTTP transport support |
| 2025-03 | Mar 2025 | OpenAI adoption, SSE improvements |
| 2025-06-18 | Jun 2025 | OAuth 2.1, Structured outputs, Elicitation |

### Future Roadmap (Anticipated)

Based on the specification update cycle, expect:
- **Q4 2025**: Enhanced streaming capabilities
- **2026**: GraphQL-like query capabilities for resources
- **2026**: Built-in caching mechanisms
- **2026**: Enhanced telemetry and observability

## Implementation Patterns

### Pattern 1: Single-Purpose Server
One server, one integration (e.g., GitHub MCP server only does GitHub)

**Advantages**:
- Simple to maintain
- Clear separation of concerns
- Easy to version and update

### Pattern 2: Multi-Purpose Server
One server, multiple integrations (e.g., "Company Data Server" with CRM, Database, Files)

**Advantages**:
- Reduced deployment complexity
- Shared authentication
- Cross-functional tools

### Pattern 3: Gateway Pattern
One MCP gateway that proxies to multiple backend MCP servers

**Advantages**:
- Centralized authentication
- Single endpoint for clients
- Load balancing and routing

Example: **MCPJungle** - Self-hosted MCP Gateway and Registry

## Performance Considerations

### Resource Usage

Based on real-world data from n8n-MCP:

| Database Adapter | Memory Usage | Performance |
|------------------|--------------|-------------|
| better-sqlite3 | ~100-120 MB | High (native) |
| sql.js | ~150-200 MB | Medium (WASM) |

**Memory Leak Warning**: Earlier implementations (pre-v2.20.2) had memory leaks causing 2.2 GB growth over 72 hours. Ensure you use updated libraries.

### Scaling Strategies

1. **Horizontal Scaling**: Run multiple instances behind a load balancer
2. **Vertical Scaling**: Increase resources for compute-heavy operations
3. **Caching**: Cache frequently accessed resources
4. **Connection Pooling**: Reuse database and API connections

## Common Use Cases

### 1. Development Tools
- Code repository access (GitHub, GitLab)
- CI/CD integration (Jenkins, GitHub Actions)
- Issue tracking (Jira, Linear)

### 2. Data Access
- Database queries (PostgreSQL, MySQL, MongoDB)
- File systems
- Cloud storage (S3, Google Drive)

### 3. Business Systems
- CRM integration (Salesforce, HubSpot)
- Analytics platforms
- Internal APIs

### 4. Workflow Automation
- n8n workflow creation and management
- Zapier-like automation
- Event processing

### 5. Knowledge Management
- Documentation systems (Confluence, Notion)
- Search engines
- Vector databases

## Technical Specifications

### JSON-RPC Protocol
MCP uses JSON-RPC 2.0 for message formatting

**Request Example**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_issue",
    "arguments": {
      "title": "Bug in authentication"
    }
  }
}
```

**Response Example**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "Issue #123 created successfully"
    }]
  }
}
```

### Content Types

MCP supports various content types:
- `text/plain`: Plain text
- `application/json`: Structured JSON data
- `image/png`, `image/jpeg`: Images (for vision models)
- `application/pdf`: PDF documents
- Custom MIME types

## References

- **Official Specification**: https://modelcontextprotocol.io/specification/latest
- **GitHub Repository**: https://github.com/modelcontextprotocol/modelcontextprotocol
- **Anthropic Announcement**: https://www.anthropic.com/news/model-context-protocol
- **Auth0 MCP Security Blog**: https://auth0.com/blog/mcp-specs-update-all-about-auth/

---

**Document Version**: 1.0
**Last Updated**: November 8, 2025
**MCP Specification**: 2025-06-18
