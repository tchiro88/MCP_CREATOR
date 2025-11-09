#!/usr/bin/env python3
"""
Slack MCP Server
Provides Model Context Protocol access to Slack workspace
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("slack-mcp")

# Get Slack credentials from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    logger.error("SLACK_BOT_TOKEN environment variable not set")
    print("Error: SLACK_BOT_TOKEN environment variable must be set", file=sys.stderr)
    print("Get your bot token from: https://api.slack.com/apps", file=sys.stderr)
    sys.exit(1)

# Initialize Slack client
slack = WebClient(token=SLACK_BOT_TOKEN)

# Initialize MCP server
mcp = FastMCP("slack", version="1.0.0")

# Verify connection on startup
try:
    auth_response = slack.auth_test()
    workspace = auth_response.get("team", "Unknown")
    bot_user = auth_response.get("user", "Unknown")
    logger.info(f"Connected to Slack workspace: {workspace}")
    logger.info(f"Bot user: {bot_user}")
    print(f"✓ Connected to Slack workspace: {workspace}")
    print(f"✓ Bot user: {bot_user}")
except SlackApiError as e:
    logger.error(f"Failed to connect to Slack: {e.response['error']}")
    print(f"Error: Failed to connect to Slack: {e.response['error']}", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# CHANNEL TOOLS
# ============================================================================

@mcp.tool()
def list_channels(include_archived: bool = False, types: str = "public_channel,private_channel") -> str:
    """
    List all channels in the workspace

    Args:
        include_archived: Include archived channels (default: False)
        types: Comma-separated channel types: public_channel, private_channel, mpim, im

    Returns:
        JSON string with list of channels
    """
    try:
        result = slack.conversations_list(
            exclude_archived=not include_archived,
            types=types,
            limit=1000
        )

        channels = []
        for channel in result["channels"]:
            channels.append({
                "id": channel["id"],
                "name": channel.get("name", "Direct Message"),
                "is_private": channel.get("is_private", False),
                "is_archived": channel.get("is_archived", False),
                "is_member": channel.get("is_member", False),
                "num_members": channel.get("num_members", 0),
                "topic": channel.get("topic", {}).get("value", ""),
                "purpose": channel.get("purpose", {}).get("value", "")
            })

        return json.dumps({
            "success": True,
            "count": len(channels),
            "channels": channels
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


@mcp.tool()
def get_channel_info(channel_id: str) -> str:
    """
    Get detailed information about a channel

    Args:
        channel_id: Channel ID (e.g., C1234567890)

    Returns:
        JSON string with channel details
    """
    try:
        result = slack.conversations_info(channel=channel_id)
        channel = result["channel"]

        return json.dumps({
            "success": True,
            "channel": {
                "id": channel["id"],
                "name": channel.get("name", "Direct Message"),
                "is_private": channel.get("is_private", False),
                "is_archived": channel.get("is_archived", False),
                "created": datetime.fromtimestamp(channel["created"]).isoformat(),
                "creator": channel.get("creator"),
                "topic": channel.get("topic", {}).get("value", ""),
                "purpose": channel.get("purpose", {}).get("value", ""),
                "num_members": channel.get("num_members", 0),
                "is_member": channel.get("is_member", False)
            }
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


# ============================================================================
# MESSAGING TOOLS
# ============================================================================

@mcp.tool()
def send_message(channel: str, text: str, thread_ts: Optional[str] = None) -> str:
    """
    Send a message to a channel or thread

    Args:
        channel: Channel ID or name (e.g., C1234567890 or #general)
        text: Message text (supports Slack markdown)
        thread_ts: Optional thread timestamp to reply to

    Returns:
        JSON string with message details
    """
    try:
        # If channel starts with #, try to find it
        if channel.startswith("#"):
            channel_name = channel[1:]
            channels_result = slack.conversations_list(types="public_channel,private_channel")
            for ch in channels_result["channels"]:
                if ch.get("name") == channel_name:
                    channel = ch["id"]
                    break

        result = slack.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )

        return json.dumps({
            "success": True,
            "message": {
                "ts": result["ts"],
                "channel": result["channel"],
                "text": text
            }
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


@mcp.tool()
def get_channel_history(channel_id: str, limit: int = 100, oldest: Optional[str] = None) -> str:
    """
    Get message history from a channel

    Args:
        channel_id: Channel ID (e.g., C1234567890)
        limit: Maximum number of messages to retrieve (default: 100, max: 1000)
        oldest: Only messages after this Unix timestamp

    Returns:
        JSON string with message history
    """
    try:
        kwargs = {
            "channel": channel_id,
            "limit": min(limit, 1000)
        }
        if oldest:
            kwargs["oldest"] = oldest

        result = slack.conversations_history(**kwargs)

        messages = []
        for msg in result["messages"]:
            messages.append({
                "ts": msg["ts"],
                "user": msg.get("user", "Unknown"),
                "text": msg.get("text", ""),
                "type": msg["type"],
                "thread_ts": msg.get("thread_ts"),
                "reply_count": msg.get("reply_count", 0),
                "timestamp": datetime.fromtimestamp(float(msg["ts"])).isoformat()
            })

        return json.dumps({
            "success": True,
            "count": len(messages),
            "messages": messages
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


@mcp.tool()
def get_thread_replies(channel_id: str, thread_ts: str) -> str:
    """
    Get all replies in a thread

    Args:
        channel_id: Channel ID (e.g., C1234567890)
        thread_ts: Thread timestamp

    Returns:
        JSON string with thread replies
    """
    try:
        result = slack.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )

        messages = []
        for msg in result["messages"]:
            messages.append({
                "ts": msg["ts"],
                "user": msg.get("user", "Unknown"),
                "text": msg.get("text", ""),
                "timestamp": datetime.fromtimestamp(float(msg["ts"])).isoformat()
            })

        return json.dumps({
            "success": True,
            "count": len(messages),
            "thread_messages": messages
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


# ============================================================================
# USER TOOLS
# ============================================================================

@mcp.tool()
def list_users(include_bots: bool = False) -> str:
    """
    List all users in the workspace

    Args:
        include_bots: Include bot users (default: False)

    Returns:
        JSON string with list of users
    """
    try:
        result = slack.users_list(limit=1000)

        users = []
        for user in result["members"]:
            if not include_bots and user.get("is_bot", False):
                continue

            if user.get("deleted", False):
                continue

            users.append({
                "id": user["id"],
                "name": user.get("name", ""),
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "email": user.get("profile", {}).get("email", ""),
                "is_admin": user.get("is_admin", False),
                "is_owner": user.get("is_owner", False),
                "status": user.get("profile", {}).get("status_text", "")
            })

        return json.dumps({
            "success": True,
            "count": len(users),
            "users": users
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


@mcp.tool()
def get_user_info(user_id: str) -> str:
    """
    Get detailed information about a user

    Args:
        user_id: User ID (e.g., U1234567890)

    Returns:
        JSON string with user details
    """
    try:
        result = slack.users_info(user=user_id)
        user = result["user"]

        return json.dumps({
            "success": True,
            "user": {
                "id": user["id"],
                "name": user.get("name", ""),
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "email": user.get("profile", {}).get("email", ""),
                "phone": user.get("profile", {}).get("phone", ""),
                "title": user.get("profile", {}).get("title", ""),
                "status": user.get("profile", {}).get("status_text", ""),
                "timezone": user.get("tz", ""),
                "is_admin": user.get("is_admin", False),
                "is_owner": user.get("is_owner", False),
                "is_bot": user.get("is_bot", False)
            }
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


# ============================================================================
# SEARCH TOOLS
# ============================================================================

@mcp.tool()
def search_messages(query: str, count: int = 20, sort: str = "timestamp") -> str:
    """
    Search for messages across the workspace

    Args:
        query: Search query (supports Slack search syntax)
        count: Maximum number of results (default: 20, max: 100)
        sort: Sort order: timestamp or score (default: timestamp)

    Returns:
        JSON string with search results
    """
    try:
        result = slack.search_messages(
            query=query,
            count=min(count, 100),
            sort=sort
        )

        messages = []
        for match in result.get("messages", {}).get("matches", []):
            messages.append({
                "text": match.get("text", ""),
                "user": match.get("user", "Unknown"),
                "username": match.get("username", "Unknown"),
                "channel": match.get("channel", {}).get("name", "Unknown"),
                "channel_id": match.get("channel", {}).get("id", ""),
                "ts": match.get("ts", ""),
                "permalink": match.get("permalink", ""),
                "timestamp": datetime.fromtimestamp(float(match.get("ts", "0"))).isoformat() if match.get("ts") else None
            })

        return json.dumps({
            "success": True,
            "total": result.get("messages", {}).get("total", 0),
            "count": len(messages),
            "messages": messages
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


# ============================================================================
# FILE TOOLS
# ============================================================================

@mcp.tool()
def upload_file(channel: str, file_path: str, title: Optional[str] = None, initial_comment: Optional[str] = None) -> str:
    """
    Upload a file to a channel

    Args:
        channel: Channel ID or name (e.g., C1234567890 or #general)
        file_path: Path to file to upload
        title: Optional file title
        initial_comment: Optional comment to add with file

    Returns:
        JSON string with upload result
    """
    try:
        # If channel starts with #, try to find it
        if channel.startswith("#"):
            channel_name = channel[1:]
            channels_result = slack.conversations_list(types="public_channel,private_channel")
            for ch in channels_result["channels"]:
                if ch.get("name") == channel_name:
                    channel = ch["id"]
                    break

        # Check if file exists
        if not os.path.exists(file_path):
            return json.dumps({
                "success": False,
                "error": f"File not found: {file_path}"
            }, indent=2)

        result = slack.files_upload_v2(
            channel=channel,
            file=file_path,
            title=title or os.path.basename(file_path),
            initial_comment=initial_comment
        )

        return json.dumps({
            "success": True,
            "file": {
                "id": result["file"]["id"],
                "name": result["file"]["name"],
                "title": result["file"]["title"],
                "permalink": result["file"]["permalink"]
            }
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def list_files(channel: Optional[str] = None, user: Optional[str] = None, count: int = 100) -> str:
    """
    List files in workspace

    Args:
        channel: Filter by channel ID (optional)
        user: Filter by user ID (optional)
        count: Maximum number of files to return (default: 100)

    Returns:
        JSON string with file list
    """
    try:
        kwargs = {"count": min(count, 1000)}
        if channel:
            kwargs["channel"] = channel
        if user:
            kwargs["user"] = user

        result = slack.files_list(**kwargs)

        files = []
        for file in result.get("files", []):
            files.append({
                "id": file["id"],
                "name": file.get("name", ""),
                "title": file.get("title", ""),
                "filetype": file.get("filetype", ""),
                "size": file.get("size", 0),
                "user": file.get("user", ""),
                "created": datetime.fromtimestamp(file.get("created", 0)).isoformat(),
                "permalink": file.get("permalink", ""),
                "url_private": file.get("url_private", "")
            })

        return json.dumps({
            "success": True,
            "count": len(files),
            "files": files
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


# ============================================================================
# REACTION TOOLS
# ============================================================================

@mcp.tool()
def add_reaction(channel: str, timestamp: str, emoji: str) -> str:
    """
    Add emoji reaction to a message

    Args:
        channel: Channel ID
        timestamp: Message timestamp
        emoji: Emoji name without colons (e.g., thumbsup, heart, fire)

    Returns:
        JSON string with result
    """
    try:
        slack.reactions_add(
            channel=channel,
            timestamp=timestamp,
            name=emoji
        )

        return json.dumps({
            "success": True,
            "message": f"Added :{emoji}: reaction"
        }, indent=2)

    except SlackApiError as e:
        return json.dumps({
            "success": False,
            "error": e.response['error']
        }, indent=2)


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("slack://channels")
def get_channels_resource() -> str:
    """Get all workspace channels"""
    return list_channels()


@mcp.resource("slack://users")
def get_users_resource() -> str:
    """Get all workspace users"""
    return list_users()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(f"Starting {mcp.name} v{mcp.version}")
    print(f"Slack Bot Token: {SLACK_BOT_TOKEN[:10]}...{SLACK_BOT_TOKEN[-10:]}")
    print("Server is ready for connections...")
    mcp.run()
