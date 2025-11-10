#!/usr/bin/env python3
"""
iCloud MCP Server
Provides Model Context Protocol access to Apple iCloud services
Supports: Mail, Calendar, Reminders, Drive, Contacts, Find My
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from mcp.server.fastmcp import FastMCP
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudAPIResponseException
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("icloud-mcp")

# Get iCloud credentials from environment
ICLOUD_USERNAME = os.getenv("ICLOUD_USERNAME")  # Apple ID email
ICLOUD_PASSWORD = os.getenv("ICLOUD_PASSWORD")  # App-specific password

if not ICLOUD_USERNAME or not ICLOUD_PASSWORD:
    logger.error("ICLOUD_USERNAME and ICLOUD_PASSWORD environment variables not set")
    print("Error: ICLOUD_USERNAME and ICLOUD_PASSWORD environment variables must be set", file=sys.stderr)
    print("Username: Your Apple ID (e.g., user@icloud.com)", file=sys.stderr)
    print("Password: App-specific password from https://appleid.apple.com", file=sys.stderr)
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP("icloud")

# Global iCloud API client
api = None

def get_icloud_api():
    """Get or initialize iCloud API client"""
    global api
    if api is None:
        try:
            api = PyiCloudService(ICLOUD_USERNAME, ICLOUD_PASSWORD)

            # Handle 2FA if required
            if api.requires_2fa:
                logger.warning("Two-factor authentication required")
                print("\n⚠️  Two-factor authentication required!", file=sys.stderr)
                print("Please use app-specific password instead of your regular password", file=sys.stderr)
                print("Generate at: https://appleid.apple.com/account/manage → Security → App-Specific Passwords", file=sys.stderr)
                sys.exit(1)

            logger.info(f"Connected to iCloud as: {ICLOUD_USERNAME}")
            print(f"✓ Connected to iCloud as: {ICLOUD_USERNAME}")

        except PyiCloudFailedLoginException as e:
            logger.error(f"Failed to login to iCloud: {e}")
            print(f"Error: Failed to login to iCloud: {e}", file=sys.stderr)
            sys.exit(1)

    return api


# ============================================================================
# CALENDAR TOOLS
# ============================================================================

@mcp.tool()
def list_calendars() -> str:
    """
    List all iCloud calendars

    Returns:
        JSON string with list of calendars
    """
    try:
        api = get_icloud_api()
        calendars = []

        for calendar in api.calendar.calendars():
            calendars.append({
                "title": calendar.get("title", ""),
                "guid": calendar.get("guid", ""),
                "color": calendar.get("color", ""),
                "enabled": calendar.get("enabled", True),
                "description": calendar.get("description", "")
            })

        return json.dumps({
            "success": True,
            "count": len(calendars),
            "calendars": calendars
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_calendar_events(calendar_title: str, days_ahead: int = 30) -> str:
    """
    Get events from a specific calendar

    Args:
        calendar_title: Calendar name (e.g., "Home", "Work")
        days_ahead: Number of days ahead to fetch (default: 30)

    Returns:
        JSON string with calendar events
    """
    try:
        api = get_icloud_api()

        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        events = api.calendar.events(start_date, end_date)

        # Filter by calendar if specified
        filtered_events = []
        for event in events:
            if calendar_title.lower() in event.get("title", "").lower() or \
               calendar_title.lower() in event.get("pGuid", "").lower():
                filtered_events.append({
                    "title": event.get("title", ""),
                    "start": event.get("startDate", [None])[1] if event.get("startDate") else None,
                    "end": event.get("endDate", [None])[1] if event.get("endDate") else None,
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "all_day": event.get("allDay", False),
                    "guid": event.get("guid", "")
                })

        return json.dumps({
            "success": True,
            "count": len(filtered_events),
            "events": filtered_events
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_calendar_event(title: str, start_time: str, end_time: str,
                         calendar: str = "Home", location: str = "",
                         description: str = "") -> str:
    """
    Create a new calendar event

    Args:
        title: Event title
        start_time: Start time (ISO format: 2025-01-15T10:00:00)
        end_time: End time (ISO format: 2025-01-15T11:00:00)
        calendar: Calendar name (default: "Home")
        location: Event location (optional)
        description: Event description (optional)

    Returns:
        JSON string with creation result
    """
    try:
        api = get_icloud_api()

        # Parse datetime
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        # Create event
        from pyicloud.services.calendar import CalendarService
        event = api.calendar.create_event(
            title=title,
            start=start_dt,
            end=end_dt,
            location=location,
            description=description
        )

        return json.dumps({
            "success": True,
            "message": f"Event '{title}' created",
            "event": {
                "title": title,
                "start": start_time,
                "end": end_time,
                "location": location
            }
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# REMINDERS TOOLS
# ============================================================================

@mcp.tool()
def list_reminders(list_name: str = "Reminders", completed: bool = False) -> str:
    """
    List reminders from a specific list

    Args:
        list_name: Reminder list name (default: "Reminders")
        completed: Include completed reminders (default: False)

    Returns:
        JSON string with reminders
    """
    try:
        api = get_icloud_api()

        reminders = []
        for reminder in api.reminders.lists.get(list_name, {}).get("reminders", []):
            if completed or not reminder.get("completed", False):
                reminders.append({
                    "title": reminder.get("title", ""),
                    "description": reminder.get("description", ""),
                    "due_date": reminder.get("dueDate", None),
                    "priority": reminder.get("priority", 0),
                    "completed": reminder.get("completed", False),
                    "guid": reminder.get("guid", "")
                })

        return json.dumps({
            "success": True,
            "list": list_name,
            "count": len(reminders),
            "reminders": reminders
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_reminder(title: str, list_name: str = "Reminders",
                   description: str = "", due_date: Optional[str] = None,
                   priority: int = 0) -> str:
    """
    Create a new reminder

    Args:
        title: Reminder title
        list_name: Reminder list name (default: "Reminders")
        description: Reminder description (optional)
        due_date: Due date (ISO format: 2025-01-15T10:00:00) (optional)
        priority: Priority 0-9, where 0=none, 1=low, 5=medium, 9=high (default: 0)

    Returns:
        JSON string with creation result
    """
    try:
        api = get_icloud_api()

        # Get the reminder list
        reminder_list = api.reminders.lists.get(list_name)
        if not reminder_list:
            return json.dumps({
                "success": False,
                "error": f"Reminder list '{list_name}' not found"
            }, indent=2)

        # Create reminder data
        reminder_data = {
            "title": title,
            "description": description,
            "priority": priority
        }

        if due_date:
            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            reminder_data["dueDate"] = due_dt.isoformat()

        # Add reminder
        api.reminders.post(list_name, reminder_data)

        return json.dumps({
            "success": True,
            "message": f"Reminder '{title}' created in '{list_name}'",
            "reminder": reminder_data
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_reminder_from_email(email_subject: str, email_from: str,
                              email_date: str, list_name: str = "Reminders",
                              due_date: Optional[str] = None) -> str:
    """
    Create a calendar reminder from an email

    Args:
        email_subject: Email subject line
        email_from: Email sender
        email_date: Email received date
        list_name: Reminder list to add to (default: "Reminders")
        due_date: Optional due date (ISO format: 2025-01-15T10:00:00)

    Returns:
        JSON string with creation result
    """
    try:
        api = get_icloud_api()

        # Create reminder title from email
        title = f"Follow up: {email_subject}"

        # Create description with email details
        description = f"From: {email_from}\nReceived: {email_date}\nSubject: {email_subject}"

        # Create the reminder
        reminder_data = {
            "title": title,
            "description": description,
            "priority": 5  # Medium priority
        }

        if due_date:
            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            reminder_data["dueDate"] = due_dt.isoformat()

        api.reminders.post(list_name, reminder_data)

        return json.dumps({
            "success": True,
            "message": f"Reminder created from email: {email_subject}",
            "reminder": reminder_data
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# MAIL TOOLS (IMAP)
# ============================================================================

def get_imap_connection():
    """Get IMAP connection to iCloud Mail"""
    try:
        imap = imaplib.IMAP4_SSL('imap.mail.me.com')
        imap.login(ICLOUD_USERNAME, ICLOUD_PASSWORD)
        return imap
    except Exception as e:
        logger.error(f"Failed to connect to iCloud Mail: {e}")
        raise


@mcp.tool()
def list_mail_folders() -> str:
    """
    List all mail folders/mailboxes

    Returns:
        JSON string with list of folders
    """
    try:
        imap = get_imap_connection()
        status, folders = imap.list()

        folder_list = []
        if status == 'OK':
            for folder in folders:
                folder_str = folder.decode('utf-8')
                # Parse folder name
                parts = folder_str.split('"')
                if len(parts) >= 3:
                    folder_list.append(parts[-2])

        imap.logout()

        return json.dumps({
            "success": True,
            "count": len(folder_list),
            "folders": folder_list
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def search_emails(folder: str = "INBOX", query: str = "ALL", max_results: int = 20) -> str:
    """
    Search emails in a folder

    Args:
        folder: Mail folder (default: "INBOX")
        query: IMAP search query (default: "ALL")
               Examples: "UNSEEN", "FROM sender@example.com", "SUBJECT meeting"
        max_results: Maximum number of emails to return (default: 20)

    Returns:
        JSON string with email list
    """
    try:
        imap = get_imap_connection()
        imap.select(folder)

        status, messages = imap.search(None, query)

        emails = []
        if status == 'OK':
            email_ids = messages[0].split()
            # Get most recent emails (reverse order)
            email_ids = email_ids[-max_results:]

            for email_id in reversed(email_ids):
                status, msg_data = imap.fetch(email_id, '(RFC822)')

                if status == 'OK':
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)

                    # Decode subject
                    subject = email_message.get('Subject', '')
                    if subject:
                        decoded = email.header.decode_header(subject)
                        subject = decoded[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                    emails.append({
                        "id": email_id.decode(),
                        "from": email_message.get('From', ''),
                        "to": email_message.get('To', ''),
                        "subject": subject,
                        "date": email_message.get('Date', ''),
                        "has_attachments": bool(email_message.get_content_maintype() == 'multipart')
                    })

        imap.logout()

        return json.dumps({
            "success": True,
            "folder": folder,
            "count": len(emails),
            "emails": emails
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_email(email_id: str, folder: str = "INBOX") -> str:
    """
    Get full email content

    Args:
        email_id: Email ID from search_emails
        folder: Mail folder (default: "INBOX")

    Returns:
        JSON string with full email content
    """
    try:
        imap = get_imap_connection()
        imap.select(folder)

        status, msg_data = imap.fetch(email_id.encode(), '(RFC822)')

        if status != 'OK':
            return json.dumps({
                "success": False,
                "error": "Email not found"
            }, indent=2)

        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Decode subject
        subject = email_message.get('Subject', '')
        if subject:
            decoded = email.header.decode_header(subject)
            subject = decoded[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

        # Get body
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        imap.logout()

        return json.dumps({
            "success": True,
            "email": {
                "id": email_id,
                "from": email_message.get('From', ''),
                "to": email_message.get('To', ''),
                "cc": email_message.get('Cc', ''),
                "subject": subject,
                "date": email_message.get('Date', ''),
                "body": body[:5000]  # Limit body length
            }
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
    """
    Send an email via iCloud Mail

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        cc: CC recipients (comma-separated) (optional)
        bcc: BCC recipients (comma-separated) (optional)

    Returns:
        JSON string with send result
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = ICLOUD_USERNAME
        msg['To'] = to
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc

        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP
        smtp = smtplib.SMTP_SSL('smtp.mail.me.com', 587)
        smtp.login(ICLOUD_USERNAME, ICLOUD_PASSWORD)

        # Send email
        recipients = [to]
        if cc:
            recipients.extend([r.strip() for r in cc.split(',')])
        if bcc:
            recipients.extend([r.strip() for r in bcc.split(',')])

        smtp.sendmail(ICLOUD_USERNAME, recipients, msg.as_string())
        smtp.quit()

        return json.dumps({
            "success": True,
            "message": f"Email sent to {to}",
            "subject": subject
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# DRIVE TOOLS
# ============================================================================

@mcp.tool()
def list_drive_files(folder_path: str = "/") -> str:
    """
    List files in iCloud Drive

    Args:
        folder_path: Folder path (default: root "/")

    Returns:
        JSON string with file list
    """
    try:
        api = get_icloud_api()

        files = []
        for item in api.drive.dir():
            files.append({
                "name": item.name,
                "type": item.type,
                "size": item.size,
                "date_modified": str(item.date_modified) if hasattr(item, 'date_modified') else None,
                "date_created": str(item.date_created) if hasattr(item, 'date_created') else None
            })

        return json.dumps({
            "success": True,
            "path": folder_path,
            "count": len(files),
            "files": files
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# CONTACTS TOOLS
# ============================================================================

@mcp.tool()
def search_contacts(query: str) -> str:
    """
    Search contacts

    Args:
        query: Search query (name, email, phone)

    Returns:
        JSON string with matching contacts
    """
    try:
        api = get_icloud_api()

        contacts = []
        for contact in api.contacts.all():
            # Search in name, email, phone
            name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
            emails = [e.get('field', '') for e in contact.get('emails', [])]
            phones = [p.get('field', '') for p in contact.get('phones', [])]

            if query.lower() in name.lower() or \
               any(query.lower() in email.lower() for email in emails) or \
               any(query in phone for phone in phones):
                contacts.append({
                    "name": name,
                    "emails": emails,
                    "phones": phones,
                    "company": contact.get('companyName', ''),
                    "notes": contact.get('notes', '')
                })

        return json.dumps({
            "success": True,
            "query": query,
            "count": len(contacts),
            "contacts": contacts
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("icloud://calendars")
def get_calendars_resource() -> str:
    """Get all iCloud calendars"""
    return list_calendars()


@mcp.resource("icloud://reminders")
def get_reminders_resource() -> str:
    """Get all reminders"""
    return list_reminders()


@mcp.resource("icloud://mail/inbox")
def get_inbox_resource() -> str:
    """Get inbox emails"""
    return search_emails(folder="INBOX", query="ALL", max_results=50)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(f"Starting {mcp.name}")
    print(f"iCloud Username: {ICLOUD_USERNAME}")

    # Initialize connection
    get_icloud_api()

    print("Server is ready for connections...")
    mcp.run()
