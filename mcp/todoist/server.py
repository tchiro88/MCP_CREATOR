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
import sys
import logging
from typing import Any, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Todoist API import
try:
    import requests
except ImportError:
    print("ERROR: requests library not installed!")
    print("Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("todoist-mcp")

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
# Initialize FastMCP Server
# ============================================================================

mcp = FastMCP(SERVER_NAME)

# ============================================================================
# MCP Resources
# ============================================================================

@mcp.resource("todoist://tasks/today")
def get_today_tasks() -> str:
    """Get today's tasks"""
    tasks = list_tasks(filter_str="today")
    return json.dumps(tasks, indent=2)

@mcp.resource("todoist://tasks/all")
def get_all_tasks() -> str:
    """Get all active tasks"""
    tasks = list_tasks()
    return json.dumps(tasks, indent=2)

@mcp.resource("todoist://projects")
def get_projects() -> str:
    """Get all projects"""
    projects = list_projects()
    return json.dumps(projects, indent=2)

# ============================================================================
# MCP Tools - Tasks
# ============================================================================

@mcp.tool()
def list_tasks_tool(project_id: Optional[str] = None, filter: Optional[str] = None) -> str:
    """
    List tasks with optional filters

    Args:
        project_id: Filter by project ID (optional)
        filter: Todoist filter string (e.g., 'today', 'priority 1', 'overdue') (optional)

    Returns:
        JSON string with task list
    """
    result = list_tasks(project_id=project_id, filter_str=filter)
    return json.dumps(result, indent=2)

@mcp.tool()
def create_task_tool(content: str, description: str = '', due_string: Optional[str] = None,
                     priority: int = 1, project_id: Optional[str] = None,
                     labels: Optional[list[str]] = None) -> str:
    """
    Create a new task

    Args:
        content: Task title/content
        description: Task description (optional)
        due_string: Due date in natural language (e.g., 'tomorrow', 'next Monday') (optional)
        priority: Priority: 1 (normal) to 4 (urgent) (optional, default: 1)
        project_id: Project ID to add task to (optional)
        labels: Array of label names (optional)

    Returns:
        JSON string with creation result
    """
    result = create_task(
        content=content,
        description=description,
        due_string=due_string,
        priority=priority,
        project_id=project_id,
        labels=labels
    )
    return json.dumps(result, indent=2)

@mcp.tool()
def update_task_tool(task_id: str, content: Optional[str] = None,
                     description: Optional[str] = None, due_string: Optional[str] = None,
                     priority: Optional[int] = None) -> str:
    """
    Update an existing task

    Args:
        task_id: Task ID to update
        content: New task content (optional)
        description: New description (optional)
        due_string: New due date (optional)
        priority: New priority 1-4 (optional)

    Returns:
        JSON string with update result
    """
    result = update_task(
        task_id=task_id,
        content=content,
        description=description,
        due_string=due_string,
        priority=priority
    )
    return json.dumps(result, indent=2)

@mcp.tool()
def complete_task_tool(task_id: str) -> str:
    """
    Mark a task as complete

    Args:
        task_id: Task ID to complete

    Returns:
        JSON string with completion result
    """
    result = complete_task(task_id)
    return json.dumps(result, indent=2)

@mcp.tool()
def delete_task_tool(task_id: str) -> str:
    """
    Delete a task

    Args:
        task_id: Task ID to delete

    Returns:
        JSON string with deletion result
    """
    result = delete_task(task_id)
    return json.dumps(result, indent=2)

# ============================================================================
# MCP Tools - Projects
# ============================================================================

@mcp.tool()
def list_projects_tool() -> str:
    """
    List all projects

    Returns:
        JSON string with project list
    """
    result = list_projects()
    return json.dumps(result, indent=2)

@mcp.tool()
def create_project_tool(name: str, color: Optional[str] = None,
                       is_favorite: bool = False) -> str:
    """
    Create a new project

    Args:
        name: Project name
        color: Color name (e.g., 'red', 'blue') (optional)
        is_favorite: Mark as favorite (optional)

    Returns:
        JSON string with creation result
    """
    result = create_project(name=name, color=color, is_favorite=is_favorite)
    return json.dumps(result, indent=2)

# ============================================================================
# MCP Tools - Comments
# ============================================================================

@mcp.tool()
def add_comment_tool(task_id: str, content: str) -> str:
    """
    Add a comment to a task

    Args:
        task_id: Task ID to comment on
        content: Comment content

    Returns:
        JSON string with addition result
    """
    result = add_task_comment(task_id=task_id, content=content)
    return json.dumps(result, indent=2)

@mcp.tool()
def get_comments_tool(task_id: str) -> str:
    """
    Get all comments for a task

    Args:
        task_id: Task ID to get comments for

    Returns:
        JSON string with comment list
    """
    result = get_task_comments(task_id)
    return json.dumps(result, indent=2)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")

    # Test API connection
    try:
        result = api_request("GET", "projects")
        if isinstance(result, dict) and 'error' in result:
            logger.error(f"Failed to connect to Todoist API: {result['error']}")
            print(f"ERROR: Failed to connect to Todoist API: {result['error']}")
            sys.exit(1)
        print(f"API Token: {TODOIST_API_TOKEN[:8]}..." if TODOIST_API_TOKEN else "No token")
        print(f"Connected to Todoist (found {len(result)} projects)")
        logger.info(f"Connected to Todoist (found {len(result)} projects)")
        print("Server is ready for connections...")

        # Run the FastMCP server on HTTP
        mcp.run()

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
