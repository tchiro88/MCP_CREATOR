#!/usr/bin/env python3
"""
MCP Integrator Server
Cross-service integration tools that aggregate data from multiple MCP servers
"""

import os
import sys
import json
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_client import MCPClient
from cross_service_tools import CrossServiceTools

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("mcp-integrator")

# Get MCP service URLs from environment
SERVICE_URLS = {
    "outlook": os.getenv('MCP_OUTLOOK_URL', 'http://mcp-outlook:3000'),
    "google": os.getenv('MCP_GOOGLE_URL', 'http://mcp-google:3000'),
    "todoist": os.getenv('MCP_TODOIST_URL', 'http://mcp-todoist:3000'),
    "slack": os.getenv('MCP_SLACK_URL', 'http://mcp-slack:3000'),
    "notion": os.getenv('MCP_NOTION_URL', 'http://mcp-notion:3000'),
    "github": os.getenv('MCP_GITHUB_URL', 'http://mcp-github:3000'),
    "homeassistant": os.getenv('MCP_HA_URL', 'http://mcp-homeassistant:3000'),
    "icloud": os.getenv('MCP_ICLOUD_URL', 'http://mcp-icloud:3000'),
}

# Initialize clients
mcp_client = MCPClient(SERVICE_URLS)
cross_service_tools = CrossServiceTools(mcp_client)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available integration tools"""
    return [
        Tool(
            name="unified_inbox",
            description="Get unified view of unread messages from ALL email/messaging services " +
                       "(Outlook, Gmail, Slack). Aggregates and sorts by date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Max messages per service (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="unified_calendar",
            description="Get unified calendar view from ALL calendar services " +
                       "(Outlook Calendar, Google Calendar). Shows all events for a date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (default: today)"
                    }
                }
            }
        ),
        Tool(
            name="unified_tasks",
            description="Get unified task list from ALL task management services " +
                       "(Todoist, Google Tasks, Notion). Shows all active tasks.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="comprehensive_briefing",
            description="Generate comprehensive daily briefing across ALL services. " +
                       "Includes: unread messages, today's calendar, tasks, and smart recommendations. " +
                       "Perfect for morning overview of everything.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_everywhere",
            description="Search for a keyword across ALL services " +
                       "(Outlook emails, Gmail, Slack messages, Notion pages, GitHub code). " +
                       "Returns aggregated results from all sources.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query/keyword"
                    },
                    "days": {
                        "type": "number",
                        "description": "Days to search back (default: 30)",
                        "default": 30
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="service_health_check",
            description="Check connectivity status of all MCP services. " +
                       "Shows which services are healthy and available.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "unified_inbox":
            limit = arguments.get("limit", 50)
            result = await cross_service_tools.unified_inbox(limit=limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "unified_calendar":
            date = arguments.get("date")
            result = await cross_service_tools.unified_calendar(date=date)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "unified_tasks":
            result = await cross_service_tools.unified_tasks()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "comprehensive_briefing":
            result = await cross_service_tools.comprehensive_briefing()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_everywhere":
            query = arguments["query"]
            days = arguments.get("days", 30)
            result = await cross_service_tools.search_everywhere(query=query, days=days)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "service_health_check":
            result = await cross_service_tools.service_health_check()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Main entry point"""
    logger.info("Starting MCP Integrator Server")

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(read_stream, write_stream, app.create_initialization_options())
        finally:
            # Cleanup
            await mcp_client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
