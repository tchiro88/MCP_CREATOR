#!/usr/bin/env node

/**
 * Simple MCP Server Example
 *
 * This is a basic MCP server that demonstrates:
 * - Tool implementation
 * - Resource exposure
 * - Prompt templates
 * - Both stdio and HTTP transports
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express from 'express';

const PORT = process.env.PORT || 3000;
const MODE = process.env.MCP_MODE || 'stdio'; // 'stdio' or 'http'

// ============================================================================
// Initialize MCP Server
// ============================================================================

const server = new Server(
  {
    name: 'simple-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

// ============================================================================
// Tools - Functions that AI can call
// ============================================================================

server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'echo',
        description: 'Echoes back the input message',
        inputSchema: {
          type: 'object',
          properties: {
            message: {
              type: 'string',
              description: 'The message to echo back',
            },
          },
          required: ['message'],
        },
      },
      {
        name: 'get_time',
        description: 'Returns the current server time',
        inputSchema: {
          type: 'object',
          properties: {
            timezone: {
              type: 'string',
              description: 'Timezone (e.g., America/New_York)',
              default: 'UTC',
            },
          },
        },
      },
      {
        name: 'calculate',
        description: 'Performs basic mathematical calculations',
        inputSchema: {
          type: 'object',
          properties: {
            operation: {
              type: 'string',
              enum: ['add', 'subtract', 'multiply', 'divide'],
              description: 'The operation to perform',
            },
            a: {
              type: 'number',
              description: 'First number',
            },
            b: {
              type: 'number',
              description: 'Second number',
            },
          },
          required: ['operation', 'a', 'b'],
        },
      },
    ],
  };
});

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'echo':
        return {
          content: [
            {
              type: 'text',
              text: `Echo: ${args.message}`,
            },
          ],
        };

      case 'get_time':
        const timezone = args.timezone || 'UTC';
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
          timeZone: timezone,
          dateStyle: 'full',
          timeStyle: 'long',
        });
        return {
          content: [
            {
              type: 'text',
              text: `Current time in ${timezone}: ${timeString}`,
            },
          ],
        };

      case 'calculate':
        const { operation, a, b } = args;
        let result;

        switch (operation) {
          case 'add':
            result = a + b;
            break;
          case 'subtract':
            result = a - b;
            break;
          case 'multiply':
            result = a * b;
            break;
          case 'divide':
            if (b === 0) {
              throw new Error('Division by zero');
            }
            result = a / b;
            break;
          default:
            throw new Error(`Unknown operation: ${operation}`);
        }

        return {
          content: [
            {
              type: 'text',
              text: `${a} ${operation} ${b} = ${result}`,
            },
          ],
        };

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// ============================================================================
// Resources - Data that AI can access
// ============================================================================

server.setRequestHandler('resources/list', async () => {
  return {
    resources: [
      {
        uri: 'config://server',
        name: 'Server Configuration',
        description: 'Current server configuration',
        mimeType: 'application/json',
      },
      {
        uri: 'status://health',
        name: 'Health Status',
        description: 'Server health and uptime',
        mimeType: 'application/json',
      },
    ],
  };
});

const serverStartTime = Date.now();

server.setRequestHandler('resources/read', async (request) => {
  const { uri } = request.params;

  switch (uri) {
    case 'config://server':
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify(
              {
                name: 'simple-mcp-server',
                version: '1.0.0',
                mode: MODE,
                port: MODE === 'http' ? PORT : 'N/A',
              },
              null,
              2
            ),
          },
        ],
      };

    case 'status://health':
      const uptime = Date.now() - serverStartTime;
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify(
              {
                status: 'healthy',
                uptime: `${Math.floor(uptime / 1000)}s`,
                timestamp: new Date().toISOString(),
              },
              null,
              2
            ),
          },
        ],
      };

    default:
      throw new Error(`Unknown resource: ${uri}`);
  }
});

// ============================================================================
// Prompts - Reusable prompt templates
// ============================================================================

server.setRequestHandler('prompts/list', async () => {
  return {
    prompts: [
      {
        name: 'greeting',
        description: 'A friendly greeting message',
        arguments: [
          {
            name: 'name',
            description: 'The name to greet',
            required: true,
          },
        ],
      },
      {
        name: 'summarize',
        description: 'Summarize the given text',
        arguments: [
          {
            name: 'text',
            description: 'The text to summarize',
            required: true,
          },
          {
            name: 'max_length',
            description: 'Maximum length of summary',
            required: false,
          },
        ],
      },
    ],
  };
});

server.setRequestHandler('prompts/get', async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case 'greeting':
      return {
        description: 'A friendly greeting',
        messages: [
          {
            role: 'user',
            content: {
              type: 'text',
              text: `Hello ${args.name}! Welcome to our MCP server. How can I assist you today?`,
            },
          },
        ],
      };

    case 'summarize':
      const maxLength = args.max_length || 100;
      return {
        description: 'Summarize text',
        messages: [
          {
            role: 'user',
            content: {
              type: 'text',
              text: `Please summarize the following text in ${maxLength} words or less:\n\n${args.text}`,
            },
          },
        ],
      };

    default:
      throw new Error(`Unknown prompt: ${name}`);
  }
});

// ============================================================================
// Start Server
// ============================================================================

async function startServer() {
  if (MODE === 'stdio') {
    console.error('Starting MCP server in stdio mode...');
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('MCP server running in stdio mode');
  } else if (MODE === 'http') {
    console.error(`Starting MCP server in HTTP mode on port ${PORT}...`);

    const app = express();

    // Health check endpoint
    app.get('/health', (req, res) => {
      res.json({
        status: 'ok',
        uptime: Math.floor((Date.now() - serverStartTime) / 1000),
        timestamp: new Date().toISOString(),
      });
    });

    // MCP SSE endpoint
    app.get('/sse', async (req, res) => {
      console.error('New SSE connection');
      const transport = new SSEServerTransport('/messages', res);
      await server.connect(transport);
    });

    // MCP messages endpoint
    app.post('/messages', express.json(), async (req, res) => {
      // Handle MCP messages
      res.json({ status: 'received' });
    });

    app.listen(PORT, () => {
      console.error(`MCP server listening on http://localhost:${PORT}`);
      console.error(`Health check: http://localhost:${PORT}/health`);
      console.error(`SSE endpoint: http://localhost:${PORT}/sse`);
    });
  } else {
    console.error(`Unknown mode: ${MODE}`);
    process.exit(1);
  }
}

// Handle errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Start the server
startServer().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
