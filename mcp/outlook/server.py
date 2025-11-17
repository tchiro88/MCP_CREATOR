"""
Outlook MCP Server - FastMCP HTTP server for Outlook.com automation.

This server provides MCP tools for interacting with Outlook.com via
browser automation using Playwright.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from fastmcp import FastMCP

from outlook_web_client import (
    OutlookWebClient,
    OutlookLoginRequiredError,
    OutlookSessionError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Outlook MCP Server")

# Configuration from environment
SESSION_DIR = Path(os.getenv("OUTLOOK_SESSION_DIR", "/app/session"))
HEADLESS = os.getenv("OUTLOOK_HEADLESS", "true").lower() == "true"
TIMEOUT = int(os.getenv("OUTLOOK_TIMEOUT", "30000"))

# Global client instance
outlook_client: OutlookWebClient | None = None


def get_client() -> OutlookWebClient:
    """
    Get or create the Outlook client instance.

    Returns:
        OutlookWebClient instance

    Raises:
        OutlookLoginRequiredError: If no valid session exists
    """
    global outlook_client

    if outlook_client is None:
        logger.info("Initializing Outlook client")
        outlook_client = OutlookWebClient(
            session_dir=SESSION_DIR,
            headless=HEADLESS,
            timeout=TIMEOUT
        )

    return outlook_client


@mcp.tool()
def session_status() -> Dict[str, Any]:
    """
    Check the current Outlook session status.

    Returns a dictionary indicating whether a valid session exists,
    session file location, and login status.

    Returns:
        Dictionary with session status information:
        - logged_in: bool - Whether currently logged in
        - session_file: str - Path to session file
        - message: str - Status message
    """
    try:
        client = get_client()
        status = client.check_session_status()

        logger.info(f"Session status checked: logged_in={status.get('logged_in', False)}")
        return status

    except Exception as e:
        logger.error(f"Error checking session status: {e}")
        return {
            "logged_in": False,
            "error": str(e),
            "message": "Failed to check session status"
        }


@mcp.tool()
def session_login() -> Dict[str, Any]:
    """
    Initiate interactive login to Outlook.com.

    For first-time setup, this requires the service to run with headless=False
    so the user can complete login and 2FA in a visible browser window.

    After successful login, the session is saved and future requests can run headless.

    Returns:
        Dictionary with login status and instructions:
        - success: bool - Whether login was successful
        - message: str - Status or instruction message
        - instructions: str - Step-by-step setup instructions (if needed)
        - session_file: str - Path to saved session (if successful)
    """
    try:
        client = get_client()
        result = client.perform_interactive_login()

        logger.info(f"Login attempt result: success={result.get('success', False)}")
        return result

    except Exception as e:
        logger.error(f"Error during login: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to perform login"
        }


@mcp.tool()
def email_list_unread(limit: int = 20) -> List[Dict[str, Any]]:
    """
    List unread emails from Outlook inbox.

    Retrieves a list of unread emails with basic information including
    sender, subject, preview, and date received.

    Args:
        limit: Maximum number of emails to return (default: 20, max: 50)

    Returns:
        List of email dictionaries, each containing:
        - id: str - Email identifier
        - subject: str - Email subject line
        - sender: str - Sender name/email
        - preview: str - Email preview text
        - date: str - Date received
        - unread: bool - Unread status (always True)

    Raises:
        OutlookLoginRequiredError: If session is invalid or expired
    """
    try:
        # Validate limit
        limit = max(1, min(limit, 50))

        client = get_client()
        emails = client.get_unread_emails(limit=limit)

        logger.info(f"Retrieved {len(emails)} unread emails")
        return emails

    except OutlookLoginRequiredError as e:
        logger.warning(f"Login required: {e}")
        return [{
            "error": "login_required",
            "message": str(e),
            "action": "Call session_login() to authenticate"
        }]

    except Exception as e:
        logger.error(f"Error listing unread emails: {e}")
        return [{
            "error": "fetch_failed",
            "message": str(e)
        }]


@mcp.tool()
def email_read(email_id: str) -> Dict[str, Any]:
    """
    Read a specific email by ID.

    Retrieves the full content of an email including body, attachments,
    and complete metadata.

    Args:
        email_id: Email identifier from email_list_unread()

    Returns:
        Dictionary containing:
        - id: str - Email identifier
        - subject: str - Email subject
        - sender: str - Sender information
        - date: str - Date received
        - body: str - Email body content
        - attachments: List - Attachment information

    Raises:
        OutlookLoginRequiredError: If session is invalid or expired
    """
    try:
        client = get_client()
        email = client.read_email(email_id)

        logger.info(f"Read email: {email_id}")
        return email

    except OutlookLoginRequiredError as e:
        logger.warning(f"Login required: {e}")
        return {
            "error": "login_required",
            "message": str(e),
            "action": "Call session_login() to authenticate"
        }

    except Exception as e:
        logger.error(f"Error reading email: {e}")
        return {
            "error": "read_failed",
            "message": str(e),
            "email_id": email_id
        }


@mcp.tool()
def email_search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search emails by query string.

    Searches through emails using Outlook's search functionality.
    Supports searching by sender, subject, content, and date.

    Args:
        query: Search query (e.g., "from:john@example.com", "subject:meeting")
        limit: Maximum results to return (default: 20, max: 50)

    Returns:
        List of matching email dictionaries, each containing:
        - id: str - Email identifier
        - subject: str - Email subject
        - sender: str - Sender information
        - preview: str - Email preview
        - date: str - Date received

    Raises:
        OutlookLoginRequiredError: If session is invalid or expired
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            return [{
                "error": "invalid_query",
                "message": "Search query cannot be empty"
            }]

        limit = max(1, min(limit, 50))

        client = get_client()
        results = client.search_emails(query=query.strip(), limit=limit)

        logger.info(f"Search for '{query}' returned {len(results)} results")
        return results

    except OutlookLoginRequiredError as e:
        logger.warning(f"Login required: {e}")
        return [{
            "error": "login_required",
            "message": str(e),
            "action": "Call session_login() to authenticate"
        }]

    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        return [{
            "error": "search_failed",
            "message": str(e),
            "query": query
        }]


@mcp.tool()
def calendar_list_today() -> List[Dict[str, Any]]:
    """
    List today's calendar events.

    Retrieves all calendar events scheduled for today from Outlook calendar.

    Returns:
        List of event dictionaries, each containing:
        - id: str - Event identifier
        - title: str - Event title
        - time: str - Event time
        - location: str - Event location
        - details: str - Additional event details

    Raises:
        OutlookLoginRequiredError: If session is invalid or expired
    """
    try:
        client = get_client()
        events = client.get_calendar_events_today()

        logger.info(f"Retrieved {len(events)} events for today")
        return events

    except OutlookLoginRequiredError as e:
        logger.warning(f"Login required: {e}")
        return [{
            "error": "login_required",
            "message": str(e),
            "action": "Call session_login() to authenticate"
        }]

    except Exception as e:
        logger.error(f"Error listing today's events: {e}")
        return [{
            "error": "fetch_failed",
            "message": str(e)
        }]


@mcp.tool()
def calendar_list_week() -> List[Dict[str, Any]]:
    """
    List this week's calendar events.

    Retrieves all calendar events scheduled for the current week
    from Outlook calendar.

    Returns:
        List of event dictionaries, each containing:
        - id: str - Event identifier
        - title: str - Event title
        - time: str - Event time/date
        - location: str - Event location
        - details: str - Additional event details

    Raises:
        OutlookLoginRequiredError: If session is invalid or expired
    """
    try:
        client = get_client()
        events = client.get_calendar_events_week()

        logger.info(f"Retrieved {len(events)} events for the week")
        return events

    except OutlookLoginRequiredError as e:
        logger.warning(f"Login required: {e}")
        return [{
            "error": "login_required",
            "message": str(e),
            "action": "Call session_login() to authenticate"
        }]

    except Exception as e:
        logger.error(f"Error listing week's events: {e}")
        return [{
            "error": "fetch_failed",
            "message": str(e)
        }]


# Cleanup on shutdown
@mcp.on_shutdown
async def cleanup():
    """Clean up resources on server shutdown."""
    global outlook_client

    if outlook_client:
        logger.info("Cleaning up Outlook client")
        try:
            outlook_client.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            outlook_client = None


if __name__ == "__main__":
    # Log startup configuration
    logger.info("=" * 60)
    logger.info("Outlook MCP Server Starting")
    logger.info("=" * 60)
    logger.info(f"Session directory: {SESSION_DIR}")
    logger.info(f"Headless mode: {HEADLESS}")
    logger.info(f"Timeout: {TIMEOUT}ms")
    logger.info("=" * 60)

    # Create session directory if it doesn't exist
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # Run the server
    mcp.run(transport="stdio")
