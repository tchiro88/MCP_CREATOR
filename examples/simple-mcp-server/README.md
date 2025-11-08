# Simple MCP Server Example

A basic Model Context Protocol (MCP) server that demonstrates core concepts including tools, resources, and prompts.

## Features

- **Tools**: Functions AI can call (echo, get_time, calculate)
- **Resources**: Data AI can access (server config, health status)
- **Prompts**: Reusable prompt templates (greeting, summarize)
- **Dual Transport**: Supports both stdio and HTTP/SSE

## Installation

```bash
npm install
```

## Running

### Stdio Mode (for Claude Desktop)

```bash
npm run start:stdio
# or
MCP_MODE=stdio node server.js
```

### HTTP Mode (for remote access)

```bash
npm run start:http
# or
MCP_MODE=http PORT=3000 node server.js
```

## Docker

### Build

```bash
docker build -t simple-mcp-server .
```

### Run

```bash
# HTTP mode
docker run -p 3000:3000 -e MCP_MODE=http simple-mcp-server

# Stdio mode
docker run -e MCP_MODE=stdio simple-mcp-server
```

## Configuration for Claude Desktop

### Stdio (Local)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `~/.config/Claude/claude_desktop_config.json` (Linux):

```json
{
  "mcpServers": {
    "simple": {
      "command": "node",
      "args": ["/path/to/simple-mcp-server/server.js"],
      "env": {
        "MCP_MODE": "stdio"
      }
    }
  }
}
```

### HTTP (Remote)

```json
{
  "mcpServers": {
    "simple-remote": {
      "url": "https://mcp.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Available Tools

### echo

Echoes back a message.

```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, MCP!"
  }
}
```

### get_time

Returns current time in specified timezone.

```json
{
  "name": "get_time",
  "arguments": {
    "timezone": "America/New_York"
  }
}
```

### calculate

Performs basic math operations.

```json
{
  "name": "calculate",
  "arguments": {
    "operation": "add",
    "a": 10,
    "b": 5
  }
}
```

## Available Resources

### config://server

Returns server configuration.

### status://health

Returns health status and uptime.

## Available Prompts

### greeting

Generate a greeting message.

```json
{
  "name": "greeting",
  "arguments": {
    "name": "Alice"
  }
}
```

### summarize

Summarize text.

```json
{
  "name": "summarize",
  "arguments": {
    "text": "Your long text here...",
    "max_length": 50
  }
}
```

## Testing

```bash
# Check health (HTTP mode only)
curl http://localhost:3000/health

# Expected output:
# {"status":"ok","uptime":123,"timestamp":"2025-11-08T..."}
```

## Extending

To add your own tools:

1. Add tool definition to `tools/list` handler
2. Implement tool logic in `tools/call` handler
3. Follow the same pattern for resources and prompts

Example:

```javascript
// In tools/list
{
  name: 'my_custom_tool',
  description: 'Does something useful',
  inputSchema: {
    type: 'object',
    properties: {
      param1: { type: 'string' }
    },
    required: ['param1']
  }
}

// In tools/call
case 'my_custom_tool':
  const result = await doSomething(args.param1);
  return {
    content: [{
      type: 'text',
      text: result
    }]
  };
```

## License

MIT
