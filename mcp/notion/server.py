#!/usr/bin/env python3
"""
Notion MCP Server
Provides access to Notion workspaces, pages, and databases

Features:
- Database queries and filtering
- Page creation and updates
- Block management (read/write content)
- Search across workspace
- User and workspace information
"""

import os
import json
import asyncio
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Notion API import
try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:
    print("ERROR: notion-client library not installed!")
    print("Install with: pip install notion-client")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

SERVER_NAME = "notion"
SERVER_VERSION = "1.0.0"

# Get Notion token from environment
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
if not NOTION_TOKEN:
    print("ERROR: NOTION_TOKEN environment variable not set!")
    print("Get your token from: https://www.notion.so/my-integrations")
    exit(1)

# Initialize Notion client
notion = Client(auth=NOTION_TOKEN)

# ============================================================================
# Database Functions
# ============================================================================

def list_databases(max_results: int = 20) -> list[dict]:
    """List all accessible databases"""
    try:
        results = notion.search(
            filter={"property": "object", "value": "database"},
            page_size=min(max_results, 100)
        )

        databases = []
        for db in results.get("results", []):
            databases.append({
                'id': db['id'],
                'title': db.get('title', [{}])[0].get('plain_text', 'Untitled') if db.get('title') else 'Untitled',
                'url': db.get('url', ''),
                'created_time': db.get('created_time', ''),
                'last_edited_time': db.get('last_edited_time', '')
            })

        return databases

    except APIResponseError as e:
        return [{'error': f'Notion API error: {e}'}]

def query_database(database_id: str, filter_obj: Optional[dict] = None,
                  sorts: Optional[list] = None, max_results: int = 20) -> list[dict]:
    """Query a database with optional filters and sorts"""
    try:
        query_params = {"page_size": min(max_results, 100)}

        if filter_obj:
            query_params["filter"] = filter_obj
        if sorts:
            query_params["sorts"] = sorts

        results = notion.databases.query(database_id=database_id, **query_params)

        pages = []
        for page in results.get("results", []):
            # Extract title from properties
            title = "Untitled"
            for prop_name, prop_value in page.get("properties", {}).items():
                if prop_value.get("type") == "title" and prop_value.get("title"):
                    title = prop_value["title"][0].get("plain_text", "Untitled")
                    break

            pages.append({
                'id': page['id'],
                'title': title,
                'url': page.get('url', ''),
                'created_time': page.get('created_time', ''),
                'last_edited_time': page.get('last_edited_time', ''),
                'properties': page.get('properties', {})
            })

        return pages

    except APIResponseError as e:
        return [{'error': f'Failed to query database: {e}'}]

# ============================================================================
# Page Functions
# ============================================================================

def get_page(page_id: str) -> dict:
    """Get page details"""
    try:
        page = notion.pages.retrieve(page_id=page_id)

        # Extract title
        title = "Untitled"
        for prop_name, prop_value in page.get("properties", {}).items():
            if prop_value.get("type") == "title" and prop_value.get("title"):
                title = prop_value["title"][0].get("plain_text", "Untitled")
                break

        return {
            'id': page['id'],
            'title': title,
            'url': page.get('url', ''),
            'created_time': page.get('created_time', ''),
            'last_edited_time': page.get('last_edited_time', ''),
            'properties': page.get('properties', {})
        }

    except APIResponseError as e:
        return {'error': f'Failed to get page: {e}'}

def create_page(parent_id: str, parent_type: str = 'database_id',
               title: str = 'Untitled', properties: Optional[dict] = None) -> dict:
    """Create a new page in a database or as a child of another page"""
    try:
        # Build parent object
        if parent_type == 'database_id':
            parent = {"database_id": parent_id}
        else:
            parent = {"page_id": parent_id}

        # Build properties with title
        page_properties = properties or {}

        # If no title property exists, try to add it
        has_title = any(prop.get('type') == 'title' for prop in page_properties.values())
        if not has_title:
            # Try common title property names
            for title_prop in ['Name', 'Title', 'name', 'title']:
                page_properties[title_prop] = {
                    "title": [{"text": {"content": title}}]
                }
                break

        page = notion.pages.create(
            parent=parent,
            properties=page_properties
        )

        return {
            'success': True,
            'id': page['id'],
            'url': page.get('url', '')
        }

    except APIResponseError as e:
        return {'error': f'Failed to create page: {e}'}

def update_page(page_id: str, properties: dict) -> dict:
    """Update page properties"""
    try:
        page = notion.pages.update(page_id=page_id, properties=properties)

        return {
            'success': True,
            'id': page['id'],
            'url': page.get('url', '')
        }

    except APIResponseError as e:
        return {'error': f'Failed to update page: {e}'}

# ============================================================================
# Block Functions
# ============================================================================

def get_page_content(page_id: str) -> dict:
    """Get all blocks (content) from a page"""
    try:
        blocks = notion.blocks.children.list(block_id=page_id)

        content = []
        for block in blocks.get("results", []):
            block_type = block.get("type", "unknown")
            block_content = block.get(block_type, {})

            # Extract text content if available
            text_content = ""
            if "rich_text" in block_content:
                text_content = " ".join([
                    rt.get("plain_text", "")
                    for rt in block_content.get("rich_text", [])
                ])

            content.append({
                'id': block['id'],
                'type': block_type,
                'content': text_content or str(block_content)[:200]
            })

        return {
            'page_id': page_id,
            'blocks': content
        }

    except APIResponseError as e:
        return {'error': f'Failed to get page content: {e}'}

def append_block_children(page_id: str, blocks: list[dict]) -> dict:
    """Append blocks to a page"""
    try:
        result = notion.blocks.children.append(block_id=page_id, children=blocks)

        return {
            'success': True,
            'blocks_added': len(result.get("results", []))
        }

    except APIResponseError as e:
        return {'error': f'Failed to append blocks: {e}'}

# ============================================================================
# Search Functions
# ============================================================================

def search_notion(query: str, filter_type: Optional[str] = None,
                 max_results: int = 20) -> list[dict]:
    """Search across Notion workspace"""
    try:
        search_params = {"query": query, "page_size": min(max_results, 100)}

        if filter_type:
            search_params["filter"] = {"property": "object", "value": filter_type}

        results = notion.search(**search_params)

        items = []
        for item in results.get("results", []):
            # Extract title based on type
            title = "Untitled"
            if item["object"] == "page":
                for prop_name, prop_value in item.get("properties", {}).items():
                    if prop_value.get("type") == "title" and prop_value.get("title"):
                        title = prop_value["title"][0].get("plain_text", "Untitled")
                        break
            elif item["object"] == "database":
                if item.get('title'):
                    title = item['title'][0].get('plain_text', 'Untitled')

            items.append({
                'id': item['id'],
                'object': item['object'],
                'title': title,
                'url': item.get('url', ''),
                'last_edited_time': item.get('last_edited_time', '')
            })

        return items

    except APIResponseError as e:
        return [{'error': f'Search failed: {e}'}]

# ============================================================================
# User Functions
# ============================================================================

def list_users(max_results: int = 20) -> list[dict]:
    """List all users in workspace"""
    try:
        results = notion.users.list(page_size=min(max_results, 100))

        users = []
        for user in results.get("results", []):
            users.append({
                'id': user['id'],
                'type': user.get('type', 'unknown'),
                'name': user.get('name', 'Unknown'),
                'avatar_url': user.get('avatar_url', '')
            })

        return users

    except APIResponseError as e:
        return [{'error': f'Failed to list users: {e}'}]

# ============================================================================
# MCP Server
# ============================================================================

app = Server(SERVER_NAME)

@app.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """List available Notion resources"""
    return [
        {
            "uri": "notion://databases",
            "name": "Databases",
            "description": "All accessible databases",
            "mimeType": "application/json"
        },
        {
            "uri": "notion://search/recent",
            "name": "Recent Pages",
            "description": "Recently edited pages",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a Notion resource"""
    if uri == "notion://databases":
        databases = list_databases()
        return json.dumps(databases, indent=2)

    elif uri == "notion://search/recent":
        results = search_notion("", max_results=20)
        return json.dumps(results, indent=2)

    raise ValueError(f"Unknown resource: {uri}")

@app.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """List available Notion tools"""
    return [
        # Database tools
        {
            "name": "list_databases",
            "description": "List all accessible databases in workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        },
        {
            "name": "query_database",
            "description": "Query a database with optional filters and sorts",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "database_id": {
                        "type": "string",
                        "description": "Database ID"
                    },
                    "filter": {
                        "type": "object",
                        "description": "Filter object (Notion API format) (optional)"
                    },
                    "sorts": {
                        "type": "array",
                        "description": "Sort array (Notion API format) (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["database_id"]
            }
        },
        # Page tools
        {
            "name": "get_page",
            "description": "Get page details and properties",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID"
                    }
                },
                "required": ["page_id"]
            }
        },
        {
            "name": "create_page",
            "description": "Create a new page in a database or as child of another page",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "parent_id": {
                        "type": "string",
                        "description": "Parent database or page ID"
                    },
                    "parent_type": {
                        "type": "string",
                        "description": "'database_id' or 'page_id' (default: 'database_id')",
                        "default": "database_id"
                    },
                    "title": {
                        "type": "string",
                        "description": "Page title (default: 'Untitled')",
                        "default": "Untitled"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Page properties object (Notion API format) (optional)"
                    }
                },
                "required": ["parent_id"]
            }
        },
        {
            "name": "update_page",
            "description": "Update page properties",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID to update"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties object to update (Notion API format)"
                    }
                },
                "required": ["page_id", "properties"]
            }
        },
        # Block/Content tools
        {
            "name": "get_page_content",
            "description": "Get all blocks (content) from a page",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID"
                    }
                },
                "required": ["page_id"]
            }
        },
        {
            "name": "append_blocks",
            "description": "Append blocks (content) to a page",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID to append to"
                    },
                    "blocks": {
                        "type": "array",
                        "description": "Array of block objects (Notion API format)"
                    }
                },
                "required": ["page_id", "blocks"]
            }
        },
        # Search tools
        {
            "name": "search",
            "description": "Search across Notion workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "filter_type": {
                        "type": "string",
                        "description": "Filter by type: 'page' or 'database' (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        },
        # User tools
        {
            "name": "list_users",
            "description": "List all users in workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict[str, Any]]:
    """Execute a Notion tool"""

    # Database tools
    if name == "list_databases":
        result = list_databases(arguments.get("max_results", 20))
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "query_database":
        result = query_database(
            database_id=arguments["database_id"],
            filter_obj=arguments.get("filter"),
            sorts=arguments.get("sorts"),
            max_results=arguments.get("max_results", 20)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Page tools
    elif name == "get_page":
        result = get_page(arguments["page_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "create_page":
        result = create_page(
            parent_id=arguments["parent_id"],
            parent_type=arguments.get("parent_type", "database_id"),
            title=arguments.get("title", "Untitled"),
            properties=arguments.get("properties")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "update_page":
        result = update_page(
            page_id=arguments["page_id"],
            properties=arguments["properties"]
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Block/Content tools
    elif name == "get_page_content":
        result = get_page_content(arguments["page_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "append_blocks":
        result = append_block_children(
            page_id=arguments["page_id"],
            blocks=arguments["blocks"]
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Search tools
    elif name == "search":
        result = search_notion(
            query=arguments["query"],
            filter_type=arguments.get("filter_type"),
            max_results=arguments.get("max_results", 20)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # User tools
    elif name == "list_users":
        result = list_users(arguments.get("max_results", 20))
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    raise ValueError(f"Unknown tool: {name}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the Notion MCP server"""
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print(f"Token: {NOTION_TOKEN[:8]}..." if NOTION_TOKEN else "No token")

    try:
        # Test connection
        notion.users.me()
        print("✓ Connected to Notion API")
        print("Server is ready for connections...")

        # Run the server
        asyncio.run(stdio_server(app))

    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()
