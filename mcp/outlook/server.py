#!/usr/bin/env python3
"""
Outlook MCP Server (Read-Only)
Provides read-only access to Outlook email and calendar with smart priority analysis
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from email_reader import OutlookEmailReader
from calendar_reader import OutlookCalendarReader
from priority_analyzer import PriorityAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("outlook-mcp")

# Get credentials from environment
OUTLOOK_EMAIL = os.getenv('OUTLOOK_EMAIL')
OUTLOOK_PASSWORD = os.getenv('OUTLOOK_PASSWORD')

# Initialize clients (lazy loading)
email_client = None
calendar_client = None
priority_analyzer = None


def get_email_client():
    """Get or create email client"""
    global email_client
    if email_client is None:
        if not OUTLOOK_EMAIL or not OUTLOOK_PASSWORD:
            raise Exception("OUTLOOK_EMAIL and OUTLOOK_PASSWORD environment variables required")
        email_client = OutlookEmailReader(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
        email_client.connect()
    return email_client


def get_calendar_client():
    """Get or create calendar client"""
    global calendar_client
    if calendar_client is None:
        if not OUTLOOK_EMAIL or not OUTLOOK_PASSWORD:
            raise Exception("OUTLOOK_EMAIL and OUTLOOK_PASSWORD environment variables required")
        calendar_client = OutlookCalendarReader(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
        calendar_client.connect()
    return calendar_client


def get_priority_analyzer():
    """Get or create priority analyzer"""
    global priority_analyzer
    if priority_analyzer is None:
        priority_analyzer = PriorityAnalyzer(get_email_client(), get_calendar_client())
    return priority_analyzer


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        # Email tools
        Tool(
            name="get_unread_emails",
            description="Get unread emails from Outlook inbox. Returns subject, sender, date, and preview.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of emails to return (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="get_recent_emails",
            description="Get recent emails from the last N days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of emails to return (default: 100)",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="search_emails",
            description="Search emails by keyword in subject or body",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keyword to search for)"
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days to search back (default: 30)",
                        "default": 30
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_email_content",
            description="Get full content of a specific email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "Email ID to retrieve"
                    }
                },
                "required": ["email_id"]
            }
        ),
        Tool(
            name="count_unread",
            description="Count total unread emails",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # Calendar tools
        Tool(
            name="get_today_events",
            description="Get today's calendar events",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_week_events",
            description="Get this week's calendar events",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_events_range",
            description="Get calendar events in a specific date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD format)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD format)"
                    }
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="search_events",
            description="Search calendar events by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keyword in event subject)"
                    },
                    "days": {
                        "type": "number",
                        "description": "Days to search forward and backward (default: 30)",
                        "default": 30
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="check_availability",
            description="Check availability for a specific day (shows free time blocks)",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check (YYYY-MM-DD format). Default: today"
                    }
                }
            }
        ),

        # Smart analysis tools
        Tool(
            name="generate_priority_list",
            description="Generate smart priority action list based on unread emails and calendar. " +
                       "Analyzes urgency, suggests time blocks, and prioritizes tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to generate list for (YYYY-MM-DD format). Default: today"
                    }
                }
            }
        ),
        Tool(
            name="daily_briefing",
            description="Generate morning briefing with today's priorities, meetings, and recommendations",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="analyze_workload",
            description="Analyze email and meeting workload over multiple days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Number of days to analyze (default: 7)",
                        "default": 7
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    try:
        # Email tools
        if name == "get_unread_emails":
            limit = arguments.get("limit", 50)
            client = get_email_client()
            emails = client.get_unread_emails(limit=limit)
            return [TextContent(type="text", text=json.dumps(emails, indent=2))]

        elif name == "get_recent_emails":
            days = arguments.get("days", 7)
            limit = arguments.get("limit", 100)
            client = get_email_client()
            emails = client.get_recent_emails(days=days, limit=limit)
            return [TextContent(type="text", text=json.dumps(emails, indent=2))]

        elif name == "search_emails":
            query = arguments["query"]
            days = arguments.get("days", 30)
            client = get_email_client()
            emails = client.search_emails(query=query, days=days)
            return [TextContent(type="text", text=json.dumps(emails, indent=2))]

        elif name == "get_email_content":
            email_id = arguments["email_id"]
            client = get_email_client()
            email = client.get_email_by_id(email_id)
            return [TextContent(type="text", text=json.dumps(email, indent=2))]

        elif name == "count_unread":
            client = get_email_client()
            count = client.count_unread()
            return [TextContent(type="text", text=json.dumps({"unread_count": count}))]

        # Calendar tools
        elif name == "get_today_events":
            client = get_calendar_client()
            events = client.get_today_events()
            return [TextContent(type="text", text=json.dumps(events, indent=2))]

        elif name == "get_week_events":
            client = get_calendar_client()
            events = client.get_week_events()
            return [TextContent(type="text", text=json.dumps(events, indent=2))]

        elif name == "get_events_range":
            start_date = datetime.fromisoformat(arguments["start_date"])
            end_date = datetime.fromisoformat(arguments["end_date"])
            client = get_calendar_client()
            events = client.get_events_range(start_date, end_date)
            return [TextContent(type="text", text=json.dumps(events, indent=2))]

        elif name == "search_events":
            query = arguments["query"]
            days = arguments.get("days", 30)
            client = get_calendar_client()
            events = client.search_events(query=query, days=days)
            return [TextContent(type="text", text=json.dumps(events, indent=2))]

        elif name == "check_availability":
            date_str = arguments.get("date")
            date = datetime.fromisoformat(date_str) if date_str else None
            client = get_calendar_client()
            availability = client.check_availability(date)
            return [TextContent(type="text", text=json.dumps(availability, indent=2))]

        # Smart analysis tools
        elif name == "generate_priority_list":
            date_str = arguments.get("date")
            date = datetime.fromisoformat(date_str) if date_str else None
            analyzer = get_priority_analyzer()
            priority_list = analyzer.generate_priority_list(date)
            return [TextContent(type="text", text=json.dumps(priority_list, indent=2))]

        elif name == "daily_briefing":
            analyzer = get_priority_analyzer()
            briefing = analyzer.daily_briefing()
            return [TextContent(type="text", text=json.dumps(briefing, indent=2))]

        elif name == "analyze_workload":
            days = arguments.get("days", 7)
            analyzer = get_priority_analyzer()
            analysis = analyzer.analyze_workload(days=days)
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Main entry point"""
    logger.info("Starting Outlook MCP Server (Read-Only)")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
