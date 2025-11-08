# n8n Integration with MCP

## Overview

n8n is an open-source workflow automation platform that can be integrated with the Model Context Protocol (MCP) to create powerful AI-driven automation workflows. This guide covers multiple integration patterns and use cases.

## What is n8n?

**n8n** is a fair-code licensed workflow automation tool that allows you to connect different services and automate tasks. Think of it as a self-hosted alternative to Zapier or Make (Integromat).

**Key Features**:
- 400+ integrations (nodes)
- Self-hosted (full data control)
- Visual workflow editor
- Code nodes for custom logic
- Webhook support
- Scheduling
- Error handling and retries

## Integration Patterns

### Pattern 1: n8n as an MCP Server

AI assistants can create, update, and manage n8n workflows via MCP.

```
┌─────────────┐
│   Claude    │
│  Desktop    │
└──────┬──────┘
       │ "Create a workflow to sync GitHub issues to Notion"
       ▼
┌──────────────────┐
│  n8n MCP Server  │
│  (czlonkowski/   │
│   n8n-mcp)       │
└──────┬───────────┘
       │ n8n API calls
       ▼
┌──────────────────┐
│  n8n Instance    │
│  (Self-hosted)   │
└──────────────────┘
```

### Pattern 2: n8n as an MCP Client

n8n workflows can call MCP servers to access AI capabilities and external tools.

```
┌──────────────────┐
│  n8n Workflow    │
│  (Triggered by   │
│   webhook/cron)  │
└──────┬───────────┘
       │ MCP Client Tool node
       ▼
┌──────────────────┐
│   MCP Server     │
│  (GitHub, DB,    │
│   custom tools)  │
└──────────────────┘
```

### Pattern 3: Hybrid Workflow Bridge

n8n acts as middleware, exposing custom business logic via MCP and consuming other MCP servers.

```
AI Assistant → n8n MCP Gateway → n8n Workflows → External MCP Servers → APIs
```

## Setup: n8n as an MCP Server

### Option 1: NPX (Fastest)

**Prerequisites**:
- Node.js 18+ installed
- n8n instance running and accessible
- n8n API key

**Installation**:
```bash
# Set environment variables
export N8N_API_URL=http://localhost:5678
export N8N_API_KEY=your-n8n-api-key

# Run n8n-MCP
npx n8n-mcp
```

**Configure Claude Desktop**:
```json
{
  "mcpServers": {
    "n8n": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "your-api-key",
        "MCP_MODE": "stdio"
      }
    }
  }
}
```

### Option 2: Docker

**Pull the image**:
```bash
docker pull ghcr.io/czlonkowski/n8n-mcp:latest
```

**Run with Docker**:
```bash
docker run -e N8N_API_URL=http://n8n:5678 \
           -e N8N_API_KEY=your-api-key \
           -e MCP_MODE=stdio \
           ghcr.io/czlonkowski/n8n-mcp:latest
```

**Docker Compose** (with n8n):
```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

  n8n-mcp:
    image: ghcr.io/czlonkowski/n8n-mcp:latest
    environment:
      - N8N_API_URL=http://n8n:5678
      - N8N_API_KEY=${N8N_API_KEY}
      - MCP_MODE=http
      - PORT=3000
    ports:
      - "3000:3000"
    depends_on:
      - n8n
    restart: unless-stopped

volumes:
  n8n_data:
```

### Option 3: Remote MCP Server

**Expose n8n-MCP via Cloudflare Tunnel**:

```yaml
# cloudflared config.yml
tunnel: <your-tunnel-id>
credentials-file: /path/to/credentials.json

ingress:
  - hostname: n8n-mcp.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404
```

**Run n8n-MCP in HTTP mode**:
```bash
docker run -p 3000:3000 \
           -e MCP_MODE=http \
           -e PORT=3000 \
           -e N8N_API_URL=http://localhost:5678 \
           -e N8N_API_KEY=your-api-key \
           ghcr.io/czlonkowski/n8n-mcp:latest
```

**Configure Claude Desktop for remote**:
```json
{
  "mcpServers": {
    "n8n-remote": {
      "url": "https://n8n-mcp.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## n8n MCP Server Capabilities

The n8n-MCP server provides AI assistants with:

### 1. Node Knowledge (541 Nodes)
- **99% property coverage**: Full access to node schemas
- **63.6% operation coverage**: Available operations per node
- **87% documentation**: Official n8n documentation
- **271 AI-capable nodes**: LangChain integration

**Example Query**:
```
User → Claude: "What properties does the GitHub node support?"
Claude → n8n MCP: get_node_info("GitHub")
n8n MCP → Claude: {properties: [...], operations: [...], docs: "..."}
```

### 2. Workflow Template Library
- **2,709 workflow templates**: Pre-built workflows from n8n.io
- **2,646 pre-extracted configurations**: Common patterns

**Example**:
```
User → Claude: "Create a workflow to backup GitHub repos to S3"
Claude → n8n MCP: search_templates("github backup s3")
n8n MCP → Claude: [template_1, template_2, ...]
Claude → User: "Found 3 relevant templates, adapting template_1..."
```

### 3. Workflow Management
- Create new workflows
- Update existing workflows
- Delete workflows
- List all workflows
- Execute workflows
- Get execution results

**Example Flow**:
```javascript
// AI creates workflow via MCP
{
  "name": "Sync GitHub Issues to Notion",
  "nodes": [
    {
      "type": "n8n-nodes-base.githubTrigger",
      "parameters": {
        "owner": "yourname",
        "repository": "yourrepo",
        "events": ["issues"]
      }
    },
    {
      "type": "n8n-nodes-base.notion",
      "parameters": {
        "operation": "create",
        "resource": "databasePage"
      }
    }
  ],
  "connections": {...}
}
```

## Setup: n8n as an MCP Client

n8n can consume MCP servers using the **MCP Client Tool** node and **MCP Server Trigger** node.

### MCP Client Tool Node

**Purpose**: Call MCP server tools from within n8n workflows

**Setup**:
1. Open n8n workflow editor
2. Add node: **MCP Client Tool**
3. Configure:
   - **MCP Server URL**: `http://localhost:3001` or `https://mcp.yourdomain.com`
   - **Tool Name**: Name of the tool to call (e.g., `create_github_issue`)
   - **Parameters**: JSON object with tool parameters

**Example Workflow**:
```
Webhook Trigger
    ↓
MCP Client Tool (GitHub MCP)
    - Tool: create_github_issue
    - Params: {title: "{{$json.title}}", body: "{{$json.body}}"}
    ↓
MCP Client Tool (Slack MCP)
    - Tool: send_message
    - Params: {channel: "#github", message: "Issue created: {{$json.url}}"}
    ↓
Return Response
```

### MCP Server Trigger Node

**Purpose**: Trigger n8n workflows when MCP server events occur

**Setup**:
1. Add node: **MCP Server Trigger**
2. Configure:
   - **MCP Server URL**: Your MCP server
   - **Event Type**: The event to listen for

**Example**:
```
MCP Server Trigger (GitHub Events)
    ↓
Filter (only "issue_opened" events)
    ↓
MCP Client Tool (Send Slack notification)
    ↓
MCP Client Tool (Create Notion page)
```

## Use Cases

### Use Case 1: AI-Powered Workflow Creation

**Scenario**: User asks Claude to create automation workflows without knowing n8n

**Flow**:
```
User: "Create a workflow that posts to Slack when I get new GitHub stars"

Claude → n8n MCP:
  1. search_templates("github stars slack")
  2. Finds relevant template
  3. create_workflow({
       name: "GitHub Stars → Slack",
       nodes: [
         {type: "githubTrigger", event: "star", ...},
         {type: "slack", operation: "postMessage", ...}
       ]
     })

n8n MCP → Claude: {workflowId: 123, url: "http://n8n/workflow/123"}
Claude → User: "Workflow created! Activate it at [URL]"
```

### Use Case 2: Data Pipeline Automation

**Scenario**: ETL pipeline with AI assistance

**Workflow**:
```
Cron Trigger (daily)
    ↓
MCP Client Tool (Database MCP)
    - Tool: query_postgres
    - Query: "SELECT * FROM users WHERE created_at > NOW() - INTERVAL '1 day'"
    ↓
Function Node (Transform data)
    ↓
MCP Client Tool (S3 MCP)
    - Tool: upload_file
    - File: transformed_data.json
    ↓
MCP Client Tool (Slack MCP)
    - Tool: send_message
    - Message: "Daily backup complete: {{$json.record_count}} users"
```

**AI Assistance**:
```
User: "Check if today's backup completed successfully"
Claude → n8n MCP: get_workflow_executions(workflowId: 123, limit: 1)
n8n MCP → Claude: {status: "success", recordCount: 450, timestamp: "..."}
Claude → User: "Today's backup completed successfully. 450 users backed up."
```

### Use Case 3: Customer Support Automation

**Scenario**: Automatically triage and respond to support tickets

**Workflow**:
```
Webhook Trigger (New Zendesk ticket)
    ↓
MCP Client Tool (AI MCP Server)
    - Tool: classify_ticket
    - Input: ticket.description
    ↓
Switch Node (Based on classification)
    ├─ Bug → MCP Client: create_github_issue
    ├─ Feature Request → MCP Client: create_notion_page
    └─ General Question → MCP Client: send_email_template
```

### Use Case 4: Multi-Platform Content Publishing

**Scenario**: Write once, publish everywhere

**Workflow**:
```
Manual Trigger (User provides content)
    ↓
MCP Client Tool (AI MCP)
    - Tool: optimize_for_platform
    - Platform: "twitter"
    ↓
MCP Client Tool (Twitter MCP)
    - Tool: create_tweet
    ↓
MCP Client Tool (AI MCP)
    - Tool: optimize_for_platform
    - Platform: "linkedin"
    ↓
MCP Client Tool (LinkedIn MCP)
    - Tool: create_post
```

**AI Integration**:
```
User: "Publish my blog post to all social media"
Claude → n8n MCP: execute_workflow(workflowId: 456, input: {content: "..."})
n8n executes workflow → Posts to Twitter, LinkedIn, Facebook
Claude → User: "Published to 3 platforms! Here are the links..."
```

## Advanced: Custom n8n MCP Bridge

Create your own n8n MCP server with custom business logic.

### Architecture

```
┌──────────────────┐
│   MCP Client     │
└────────┬─────────┘
         │ HTTP/stdio
         ▼
┌──────────────────┐
│ Custom n8n MCP   │
│     Bridge       │
└────────┬─────────┘
         │
         ├─→ n8n API (workflow management)
         ├─→ Custom Business Logic
         └─→ Database/Cache
```

### Example Implementation

```javascript
// custom-n8n-mcp-server.js
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import axios from 'axios';

const N8N_API_URL = process.env.N8N_API_URL || 'http://localhost:5678';
const N8N_API_KEY = process.env.N8N_API_KEY;

const server = new Server({
  name: 'custom-n8n-mcp',
  version: '1.0.0',
});

// Register tools
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'execute_workflow',
        description: 'Execute an n8n workflow with custom parameters',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: { type: 'string' },
            data: { type: 'object' },
          },
          required: ['workflowId'],
        },
      },
      {
        name: 'create_workflow_from_template',
        description: 'Create workflow from predefined template',
        inputSchema: {
          type: 'object',
          properties: {
            templateName: { type: 'string' },
            config: { type: 'object' },
          },
          required: ['templateName'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  if (name === 'execute_workflow') {
    const response = await axios.post(
      `${N8N_API_URL}/api/v1/workflows/${args.workflowId}/execute`,
      args.data,
      {
        headers: {
          'X-N8N-API-KEY': N8N_API_KEY,
        },
      }
    );

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(response.data, null, 2),
        },
      ],
    };
  }

  if (name === 'create_workflow_from_template') {
    // Custom logic: load template, customize, create workflow
    const template = loadTemplate(args.templateName);
    const customized = customizeTemplate(template, args.config);

    const response = await axios.post(
      `${N8N_API_URL}/api/v1/workflows`,
      customized,
      {
        headers: {
          'X-N8N-API-KEY': N8N_API_KEY,
        },
      }
    );

    return {
      content: [
        {
          type: 'text',
          text: `Workflow created: ${N8N_API_URL}/workflow/${response.data.id}`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Run Custom Bridge

```bash
node custom-n8n-mcp-server.js
```

### Configure in Claude Desktop

```json
{
  "mcpServers": {
    "custom-n8n": {
      "command": "node",
      "args": ["/path/to/custom-n8n-mcp-server.js"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "your-api-key"
      }
    }
  }
}
```

## n8n API Key Setup

### Generate API Key

1. Open n8n (http://localhost:5678)
2. Go to: Settings → API
3. Click: "Create API Key"
4. Copy the key

### Secure API Key Storage

**Option 1: Environment Variable**
```bash
export N8N_API_KEY=your-api-key-here
```

**Option 2: .env File**
```bash
# .env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your-api-key-here
```

**Option 3: Secret Management**
```bash
# Using pass (password store)
pass insert n8n/api-key

# Retrieve
export N8N_API_KEY=$(pass n8n/api-key)
```

## Security Considerations

### 1. API Key Protection

- ✅ Never commit API keys to Git
- ✅ Use environment variables
- ✅ Rotate keys regularly
- ✅ Use different keys for dev/prod

### 2. n8n MCP Server Security

If exposing n8n-MCP remotely:

```yaml
# Cloudflare Zero Trust Access Policy
Application: n8n-mcp.yourdomain.com
Policies:
  - Allow: Your email only
  - Require: 2FA
  - Session: 8 hours
```

### 3. Workflow Validation

**Safety Warning from n8n-MCP**:
> "NEVER edit your production workflows directly with AI!"

**Best Practices**:
1. Test workflows in development environment
2. Export backups before AI modifications
3. Review AI-generated workflows manually
4. Use version control for workflows

### 4. Rate Limiting

```javascript
// Add to custom MCP server
const rateLimit = new Map();

function checkRateLimit(clientId) {
  const now = Date.now();
  const requests = rateLimit.get(clientId) || [];
  const recentRequests = requests.filter(t => now - t < 60000); // 1 minute

  if (recentRequests.length >= 100) {
    throw new Error('Rate limit exceeded');
  }

  recentRequests.push(now);
  rateLimit.set(clientId, recentRequests);
}
```

## Monitoring & Telemetry

### Disable n8n-MCP Telemetry

```bash
export N8N_MCP_TELEMETRY_DISABLED=true
```

Or:
```bash
npx n8n-mcp --disable-telemetry
```

### Monitor n8n Workflow Executions

**Via n8n API**:
```bash
curl -X GET http://localhost:5678/api/v1/executions \
  -H "X-N8N-API-KEY: your-api-key"
```

**Via MCP**:
```
User → Claude: "Show me failed workflow executions from the last 24 hours"
Claude → n8n MCP: list_executions(status: "error", since: "24h")
```

## Performance Optimization

### Memory Usage

Based on n8n-MCP benchmarks:

| Database | Memory Usage | Notes |
|----------|--------------|-------|
| better-sqlite3 | 100-120 MB | Default in Docker, native performance |
| sql.js | 150-200 MB | JavaScript fallback, WASM-based |

**Recommendation**: Use better-sqlite3 for production.

### Caching

```javascript
// Add caching to reduce n8n API calls
const NodeCache = require('node-cache');
const cache = new NodeCache({ stdTTL: 600 }); // 10 minutes

async function getWorkflow(workflowId) {
  const cached = cache.get(`workflow_${workflowId}`);
  if (cached) return cached;

  const workflow = await fetchFromN8N(workflowId);
  cache.set(`workflow_${workflowId}`, workflow);
  return workflow;
}
```

## Troubleshooting

### Issue: n8n-MCP Can't Connect to n8n

**Check**:
```bash
# Verify n8n is running
curl http://localhost:5678/healthz

# Verify API key
curl -H "X-N8N-API-KEY: your-key" http://localhost:5678/api/v1/workflows
```

### Issue: Memory Leak

**Symptoms**: Memory usage grows over time (pre-v2.20.2)

**Solution**: Update to latest version:
```bash
docker pull ghcr.io/czlonkowski/n8n-mcp:latest
```

### Issue: Claude Can't Find n8n Tools

**Check Claude Desktop config**:
```bash
# macOS
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
cat ~/.config/Claude/claude_desktop_config.json
```

**Restart Claude Desktop** after config changes.

## Resources

- **n8n-MCP GitHub**: https://github.com/czlonkowski/n8n-mcp
- **n8n Documentation**: https://docs.n8n.io
- **n8n Workflow Templates**: https://n8n.io/workflows
- **MCP Client Tool**: https://n8n.io/integrations/mcp-client-tool/
- **n8n Community**: https://community.n8n.io

---

**Document Version**: 1.0
**Last Updated**: November 8, 2025
