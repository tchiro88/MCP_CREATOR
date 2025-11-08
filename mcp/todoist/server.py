#!/usr/bin/env python3
"""
Todoist MCP Server
Provides access to Todoist tasks, projects, and labels

Features:
- List tasks (with filters)
- Create, update, complete tasks
- Manage projects
- Add comments
- Search tasks
"""

import os
import json
import asyncio
from typing import Any, Optional
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Todoist API import
try:
    import requests
except ImportError:
    print("ERROR: requests library not installed!")
    print("Install with: pip install requests")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

SERVER_NAME = "todoist"
SERVER_VERSION = "1.0.0"

# Get API token from environment
TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')
if not TODOIST_API_TOKEN:
    print("ERROR: TODOIST_API_TOKEN environment variable not set!")
    print("Get your token from: https://todoist.com/prefs/integrations")
    exit(1)

# Todoist REST API base URL
BASE_URL = "https://api.todoist.com/rest/v2"

# Common headers
HEADERS = {
    "Authorization": f"Bearer {TODOIST_API_TOKEN}",
    "Content-Type": "application/json"
}

# ============================================================================
# Todoist API Functions
# ============================================================================

def api_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make a request to Todoist API"""
    url = f"{BASE_URL}/{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, params=data)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        response.raise_for_status()

        # DELETE returns empty response
        if method == "DELETE":
            return {"success": True}

        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# ============================================================================
# Task Functions
# ============================================================================

def list_tasks(project_id: Optional[str] = None, filter_str: Optional[str] = None) -> list[dict]:
    """List tasks with optional filters"""
    params = {}

    if project_id:
        params['project_id'] = project_id
    if filter_str:
        params['filter'] = filter_str

    result = api_request("GET", "tasks", params)

    if isinstance(result, dict) and 'error' in result:
        return [result]

    # Format tasks for readability
    tasks = []
    for task in result:
        tasks.append({
            'id': task['id'],
            'content': task['content'],
            'description': task.get('description', ''),
            'priority': task['priority'],
            'due': task.get('due', {}).get('string', 'No due date'),
            'project_id': task['project_id'],
            'labels': task.get('labels', []),
            'url': task['url']
        })

    return tasks

def create_task(content: str, description: str = '', due_string: Optional[str] = None,
                priority: int = 1, project_id: Optional[str] = None,
                labels: Optional[list[str]] = None) -> dict:
    """Create a new task"""
    data = {
        'content': content,
        'description': description,
        'priority': priority
    }

    if due_string:
        data['due_string'] = due_string
    if project_id:
        data['project_id'] = project_id
    if labels:
        data['labels'] = labels

    result = api_request("POST", "tasks", data)

    if 'error' in result:
        return result

    return {
        'success': True,
        'task_id': result['id'],
        'content': result['content'],
        'url': result['url']
    }

def update_task(task_id: str, content: Optional[str] = None,
                description: Optional[str] = None, due_string: Optional[str] = None,
                priority: Optional[int] = None) -> dict:
    """Update an existing task"""
    data = {}

    if content:
        data['content'] = content
    if description is not None:
        data['description'] = description
    if due_string:
        data['due_string'] = due_string
    if priority:
        data['priority'] = priority

    result = api_request("POST", f"tasks/{task_id}", data)

    if 'error' in result:
        return result

    return {
        'success': True,
        'task_id': result['id'],
        'updated': True
    }

def complete_task(task_id: str) -> dict:
    """Complete a task"""
    result = api_request("POST", f"tasks/{task_id}/close")

    if 'error' in result:
        return result

    return {
        'success': True,
        'task_id': task_id,
        'completed': True
    }

def delete_task(task_id: str) -> dict:
    """Delete a task"""
    result = api_request("DELETE", f"tasks/{task_id}")
    return result

# ============================================================================
# Project Functions
# ============================================================================

def list_projects() -> list[dict]:
    """List all projects"""
    result = api_request("GET", "projects")

    if isinstance(result, dict) and 'error' in result:
        return [result]

    projects = []
    for project in result:
        projects.append({
            'id': project['id'],
            'name': project['name'],
            'color': project.get('color', ''),
            'is_favorite': project.get('is_favorite', False),
            'url': project['url']
        })

    return projects

def create_project(name: str, color: Optional[str] = None,
                  is_favorite: bool = False) -> dict:
    """Create a new project"""
    data = {
        'name': name,
        'is_favorite': is_favorite
    }

    if color:
        data['color'] = color

    result = api_request("POST", "projects", data)

    if 'error' in result:
        return result

    return {
        'success': True,
        'project_id': result['id'],
        'name': result['name'],
        'url': result['url']
    }

# ============================================================================
# Comment Functions
# ============================================================================

def add_task_comment(task_id: str, content: str) -> dict:
    """Add a comment to a task"""
    data = {
        'task_id': task_id,
        'content': content
    }

    result = api_request("POST", "comments", data)

    if 'error' in result:
        return result

    return {
        'success': True,
        'comment_id': result['id'],
        'task_id': task_id
    }

def get_task_comments(task_id: str) -> list[dict]:
    """Get all comments for a task"""
    result = api_request("GET", "comments", {'task_id': task_id})

    if isinstance(result, dict) and 'error' in result:
        return [result]

    comments = []
    for comment in result:
        comments.append({
            'id': comment['id'],
            'content': comment['content'],
            'posted_at': comment['posted_at']
        })

    return comments

# ============================================================================
# MCP Server
# ============================================================================

app = Server(SERVER_NAME)

@app.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """List available Todoist resources"""
    return [
        {
            "uri": "todoist://tasks/today",
            "name": "Today's Tasks",
            "description": "All tasks due today",
            "mimeType": "application/json"
        },
        {
            "uri": "todoist://tasks/all",
            "name": "All Tasks",
            "description": "All active tasks",
            "mimeType": "application/json"
        },
        {
            "uri": "todoist://projects",
            "name": "Projects",
            "description": "All Todoist projects",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a Todoist resource"""
    if uri == "todoist://tasks/today":
        tasks = list_tasks(filter_str="today")
        return json.dumps(tasks, indent=2)

    elif uri == "todoist://tasks/all":
        tasks = list_tasks()
        return json.dumps(tasks, indent=2)

    elif uri == "todoist://projects":
        projects = list_projects()
        return json.dumps(projects, indent=2)

    raise ValueError(f"Unknown resource: {uri}")

@app.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """List available Todoist tools"""
    return [
        # Task tools
        {
            "name": "list_tasks",
            "description": "List tasks with optional filters",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Filter by project ID (optional)"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Todoist filter string (e.g., 'today', 'priority 1', 'overdue') (optional)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "create_task",
            "description": "Create a new task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Task title/content"
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description (optional)"
                    },
                    "due_string": {
                        "type": "string",
                        "description": "Due date in natural language (e.g., 'tomorrow', 'next Monday', '2025-11-10') (optional)"
                    },
                    "priority": {
                        "type": "number",
                        "description": "Priority: 1 (normal) to 4 (urgent) (optional, default: 1)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID to add task to (optional)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of label names (optional)"
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "update_task",
            "description": "Update an existing task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to update"
                    },
                    "content": {
                        "type": "string",
                        "description": "New task content (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "due_string": {
                        "type": "string",
                        "description": "New due date (optional)"
                    },
                    "priority": {
                        "type": "number",
                        "description": "New priority 1-4 (optional)"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "complete_task",
            "description": "Mark a task as complete",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to complete"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "delete_task",
            "description": "Delete a task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to delete"
                    }
                },
                "required": ["task_id"]
            }
        },
        # Project tools
        {
            "name": "list_projects",
            "description": "List all projects",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "create_project",
            "description": "Create a new project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "color": {
                        "type": "string",
                        "description": "Color name (e.g., 'red', 'blue') (optional)"
                    },
                    "is_favorite": {
                        "type": "boolean",
                        "description": "Mark as favorite (optional)"
                    }
                },
                "required": ["name"]
            }
        },
        # Comment tools
        {
            "name": "add_comment",
            "description": "Add a comment to a task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to comment on"
                    },
                    "content": {
                        "type": "string",
                        "description": "Comment content"
                    }
                },
                "required": ["task_id", "content"]
            }
        },
        {
            "name": "get_comments",
            "description": "Get all comments for a task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to get comments for"
                    }
                },
                "required": ["task_id"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict[str, Any]]:
    """Execute a Todoist tool"""

    # Task tools
    if name == "list_tasks":
        result = list_tasks(
            project_id=arguments.get("project_id"),
            filter_str=arguments.get("filter")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "create_task":
        result = create_task(
            content=arguments["content"],
            description=arguments.get("description", ""),
            due_string=arguments.get("due_string"),
            priority=arguments.get("priority", 1),
            project_id=arguments.get("project_id"),
            labels=arguments.get("labels")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "update_task":
        result = update_task(
            task_id=arguments["task_id"],
            content=arguments.get("content"),
            description=arguments.get("description"),
            due_string=arguments.get("due_string"),
            priority=arguments.get("priority")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "complete_task":
        result = complete_task(arguments["task_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "delete_task":
        result = delete_task(arguments["task_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Project tools
    elif name == "list_projects":
        result = list_projects()
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "create_project":
        result = create_project(
            name=arguments["name"],
            color=arguments.get("color"),
            is_favorite=arguments.get("is_favorite", False)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Comment tools
    elif name == "add_comment":
        result = add_task_comment(
            task_id=arguments["task_id"],
            content=arguments["content"]
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "get_comments":
        result = get_task_comments(arguments["task_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    raise ValueError(f"Unknown tool: {name}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the Todoist MCP server"""
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print(f"API Token: {TODOIST_API_TOKEN[:8]}..." if TODOIST_API_TOKEN else "No token")

    # Test API connection
    try:
        result = api_request("GET", "projects")
        if isinstance(result, dict) and 'error' in result:
            print(f"ERROR: Failed to connect to Todoist API: {result['error']}")
            exit(1)
        print(f"✓ Connected to Todoist (found {len(result)} projects)")
        print("Server is ready for connections...")

        # Run the server
        asyncio.run(stdio_server(app))

    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()
