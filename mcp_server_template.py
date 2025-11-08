#!/usr/bin/env python3
"""
MCP Server Template
A starting point for building custom MCP servers

Usage:
1. Copy this file to your project
2. Rename the server
3. Add your resources, tools, and prompts
4. Test locally, then connect to Claude Desktop
"""

import json
import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server

# ============================================================================
# Configuration
# ============================================================================

SERVER_NAME = "my-custom-server"
SERVER_VERSION = "0.1.0"

# ============================================================================
# Create Server Instance
# ============================================================================

app = Server(SERVER_NAME)

# ============================================================================
# Resources - Data/Content Access
# ============================================================================

@app.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """
    List all available resources.

    Resources are READ-ONLY data sources that agents can access.
    Think of these like GET endpoints in a REST API.

    Return format:
    [
        {
            "uri": "unique://identifier",
            "name": "Human-readable name",
            "description": "What this resource provides",
            "mimeType": "application/json" or "text/plain" etc.
        }
    ]
    """
    return [
        {
            "uri": "example://data",
            "name": "Example Data",
            "description": "Sample data resource",
            "mimeType": "application/json"
        },
        # Add more resources here
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    Read a specific resource by URI.

    Args:
        uri: The resource identifier

    Returns:
        String content (JSON, text, etc.)

    Raises:
        ValueError: If resource not found
    """
    if uri == "example://data":
        data = {
            "message": "Hello from MCP",
            "timestamp": "2025-11-07",
            "version": SERVER_VERSION
        }
        return json.dumps(data, indent=2)

    # Add more resource handlers here
    # elif uri == "another://resource":
    #     return load_resource_data()

    raise ValueError(f"Unknown resource: {uri}")


# ============================================================================
# Tools - Actions/Functions
# ============================================================================

@app.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """
    List all available tools.

    Tools are ACTIONS that agents can execute.
    Think of these like POST/PUT/DELETE endpoints in a REST API.

    Return format:
    [
        {
            "name": "tool_name",
            "description": "What this tool does",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        }
    ]
    """
    return [
        {
            "name": "echo",
            "description": "Echo back a message",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo back"
                    }
                },
                "required": ["message"]
            }
        },
        # Add more tools here
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict[str, Any]]:
    """
    Execute a tool.

    Args:
        name: Tool name
        arguments: Tool parameters as dict

    Returns:
        List of content blocks (text, image, etc.)

    Raises:
        ValueError: If tool not found
    """
    if name == "echo":
        message = arguments.get("message", "")
        return [
            {
                "type": "text",
                "text": f"Echo: {message}"
            }
        ]

    # Add more tool handlers here
    # elif name == "another_tool":
    #     result = execute_tool(arguments)
    #     return [{"type": "text", "text": str(result)}]

    raise ValueError(f"Unknown tool: {name}")


# ============================================================================
# Prompts - Templates (Optional)
# ============================================================================

@app.list_prompts()
async def list_prompts() -> list[dict[str, Any]]:
    """
    List all available prompts.

    Prompts are reusable templates with placeholders.
    These help standardize common tasks.

    Return format:
    [
        {
            "name": "prompt_name",
            "description": "What this prompt helps with",
            "arguments": [
                {
                    "name": "arg_name",
                    "description": "Argument description",
                    "required": True
                }
            ]
        }
    ]
    """
    return [
        {
            "name": "example_prompt",
            "description": "Example prompt template",
            "arguments": [
                {
                    "name": "topic",
                    "description": "Topic to discuss",
                    "required": True
                }
            ]
        }
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> dict[str, Any]:
    """
    Get a prompt with filled-in arguments.

    Args:
        name: Prompt name
        arguments: Values for prompt placeholders

    Returns:
        Prompt with messages

    Raises:
        ValueError: If prompt not found
    """
    if name == "example_prompt":
        topic = arguments.get("topic", "general")
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Let's discuss {topic}. Please provide detailed information."
                    }
                }
            ]
        }

    raise ValueError(f"Unknown prompt: {name}")


# ============================================================================
# Helper Functions
# ============================================================================

def load_data(source: str) -> dict:
    """Load data from a source (file, database, API)"""
    # Implement your data loading logic
    pass


def execute_action(action: str, params: dict) -> Any:
    """Execute an action with parameters"""
    # Implement your action logic
    pass


def format_response(data: Any) -> str:
    """Format data for response"""
    if isinstance(data, dict) or isinstance(data, list):
        return json.dumps(data, indent=2)
    return str(data)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the MCP server"""
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print("Server is ready for connections...")

    # Run the server with stdio transport
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()


# ============================================================================
# Testing
# ============================================================================

"""
To test this server:

1. Make executable:
   chmod +x mcp_server_template.py

2. Install dependencies:
   pip install mcp

3. Run directly (will wait for MCP client):
   python mcp_server_template.py

4. Or test with Python:
   python -i mcp_server_template.py
   # Then interact with app object

5. Connect to Claude Desktop:
   Edit: ~/Library/Application Support/Claude/claude_desktop_config.json

   {
     "mcpServers": {
       "my-server": {
         "command": "python",
         "args": ["/full/path/to/mcp_server_template.py"]
       }
     }
   }

   Restart Claude Desktop and test!

Example questions to ask Claude:
- "What resources do you have access to?"
- "Show me the example data"
- "Echo the message: Hello World"
"""


# ============================================================================
# Next Steps
# ============================================================================

"""
Customize this template:

1. Resources:
   - Connect to your data sources (files, databases, APIs)
   - Add resource types: documents, images, real-time data
   - Implement proper error handling

2. Tools:
   - Add actions relevant to your domain
   - Integrate with external APIs
   - Add proper validation and error handling

3. Prompts:
   - Create templates for common workflows
   - Add domain-specific prompts
   - Include examples and best practices

4. Security:
   - Add authentication if needed
   - Validate all inputs
   - Sanitize outputs
   - Rate limiting if exposed over HTTP

5. Error Handling:
   - Add try-except blocks
   - Return meaningful error messages
   - Log errors for debugging

6. Testing:
   - Write unit tests for each function
   - Test with Claude Desktop
   - Test error cases

7. Documentation:
   - Document each resource/tool/prompt
   - Add usage examples
   - Create a README
"""
