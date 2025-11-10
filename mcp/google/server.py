#!/usr/bin/env python3
"""
Google Services MCP Server
Provides access to Gmail, Google Drive, Google Calendar, and Google Photos

Features:
- Gmail: Read, search, send emails
- Google Drive: List, search, read, upload files
- Calendar: List events, create events, search calendar
- Photos: List albums, search photos, view photo details
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from email.mime.text import MIMEText
    import base64
except ImportError:
    print("ERROR: Google API libraries not installed!")
    print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

SERVER_NAME = "google-services"
SERVER_VERSION = "1.0.0"

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    # Removed photoslibrary scope - causing OAuth errors
    # 'https://www.googleapis.com/auth/photoslibrary.readonly',
]

# File paths
TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

# ============================================================================
# Google API Authentication
# ============================================================================

def get_credentials() -> Optional[Credentials]:
    """Get valid Google API credentials"""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Credentials file not found: {CREDENTIALS_FILE}\n"
                    "Please download it from Google Cloud Console"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds

# ============================================================================
# Gmail Functions
# ============================================================================

def gmail_search(query: str = '', max_results: int = 10) -> list[dict]:
    """Search Gmail messages"""
    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        detailed_messages = []

        for msg in messages:
            detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in detail['payload']['headers']}

            # Get snippet and body
            snippet = detail.get('snippet', '')
            body = get_message_body(detail['payload'])

            detailed_messages.append({
                'id': detail['id'],
                'threadId': detail['threadId'],
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'snippet': snippet,
                'body': body[:500] if body else snippet  # Limit body size
            })

        return detailed_messages

    except HttpError as error:
        return [{'error': f'Gmail API error: {error}'}]

def get_message_body(payload: dict) -> str:
    """Extract message body from payload"""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')

    if 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data).decode('utf-8')

    return ''

def gmail_send(to: str, subject: str, body: str) -> dict:
    """Send an email via Gmail"""
    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        return {
            'success': True,
            'messageId': result['id'],
            'threadId': result['threadId']
        }

    except HttpError as error:
        return {'error': f'Failed to send email: {error}'}

# ============================================================================
# Google Drive Functions
# ============================================================================

def drive_list_files(query: str = '', max_results: int = 20) -> list[dict]:
    """List files in Google Drive"""
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)

        results = service.files().list(
            pageSize=max_results,
            q=query,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
        ).execute()

        files = results.get('files', [])

        return [{
            'id': f['id'],
            'name': f['name'],
            'mimeType': f['mimeType'],
            'size': f.get('size', 'N/A'),
            'created': f['createdTime'],
            'modified': f['modifiedTime'],
            'link': f.get('webViewLink', '')
        } for f in files]

    except HttpError as error:
        return [{'error': f'Drive API error: {error}'}]

def drive_search_files(name: str) -> list[dict]:
    """Search for files by name"""
    query = f"name contains '{name}'"
    return drive_list_files(query=query)

def drive_get_file_content(file_id: str) -> dict:
    """Get file metadata and content (for text files)"""
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)

        # Get metadata
        metadata = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, description, webViewLink"
        ).execute()

        result = {
            'id': metadata['id'],
            'name': metadata['name'],
            'mimeType': metadata['mimeType'],
            'size': metadata.get('size', 'N/A'),
            'description': metadata.get('description', ''),
            'link': metadata.get('webViewLink', '')
        }

        # Try to get content for text files
        if metadata['mimeType'].startswith('text/'):
            content = service.files().get_media(fileId=file_id).execute()
            result['content'] = content.decode('utf-8')[:1000]  # Limit size

        return result

    except HttpError as error:
        return {'error': f'Failed to get file: {error}'}

# ============================================================================
# Google Calendar Functions
# ============================================================================

def calendar_list_events(max_results: int = 10, days_ahead: int = 7) -> list[dict]:
    """List upcoming calendar events"""
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        return [{
            'id': event['id'],
            'summary': event.get('summary', 'No title'),
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'end': event['end'].get('dateTime', event['end'].get('date')),
            'location': event.get('location', ''),
            'description': event.get('description', '')[:200],  # Limit size
            'attendees': [a['email'] for a in event.get('attendees', [])]
        } for event in events]

    except HttpError as error:
        return [{'error': f'Calendar API error: {error}'}]

def calendar_create_event(summary: str, start_time: str, end_time: str,
                         description: str = '', location: str = '') -> dict:
    """Create a new calendar event"""
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }

        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        return {
            'success': True,
            'eventId': created_event['id'],
            'htmlLink': created_event.get('htmlLink', '')
        }

    except HttpError as error:
        return {'error': f'Failed to create event: {error}'}

# ============================================================================
# Google Photos Functions
# ============================================================================

def photos_list_albums(max_results: int = 20) -> list[dict]:
    """List photo albums"""
    try:
        creds = get_credentials()
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

        results = service.albums().list(
            pageSize=min(max_results, 50)
        ).execute()

        albums = results.get('albums', [])

        return [{
            'id': album['id'],
            'title': album.get('title', 'Untitled'),
            'productUrl': album.get('productUrl', ''),
            'mediaItemsCount': album.get('mediaItemsCount', 'Unknown'),
            'coverPhotoUrl': album.get('coverPhotoBaseUrl', '')
        } for album in albums]

    except HttpError as error:
        return [{'error': f'Photos API error: {error}'}]

def photos_search(album_id: Optional[str] = None, max_results: int = 20) -> list[dict]:
    """Search for photos, optionally in a specific album"""
    try:
        creds = get_credentials()
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

        body = {
            'pageSize': min(max_results, 100)
        }

        if album_id:
            body['albumId'] = album_id

        results = service.mediaItems().search(body=body).execute()

        items = results.get('mediaItems', [])

        return [{
            'id': item['id'],
            'filename': item.get('filename', 'Unknown'),
            'mimeType': item.get('mimeType', ''),
            'creationTime': item.get('mediaMetadata', {}).get('creationTime', ''),
            'width': item.get('mediaMetadata', {}).get('width', ''),
            'height': item.get('mediaMetadata', {}).get('height', ''),
            'productUrl': item.get('productUrl', ''),
            'baseUrl': item.get('baseUrl', '')
        } for item in items]

    except HttpError as error:
        return [{'error': f'Photos search error: {error}'}]

def photos_get_media_item(media_id: str) -> dict:
    """Get details of a specific photo/video"""
    try:
        creds = get_credentials()
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

        item = service.mediaItems().get(mediaItemId=media_id).execute()

        metadata = item.get('mediaMetadata', {})

        return {
            'id': item['id'],
            'filename': item.get('filename', ''),
            'mimeType': item.get('mimeType', ''),
            'productUrl': item.get('productUrl', ''),
            'baseUrl': item.get('baseUrl', ''),
            'description': item.get('description', ''),
            'creationTime': metadata.get('creationTime', ''),
            'width': metadata.get('width', ''),
            'height': metadata.get('height', ''),
            'photo': metadata.get('photo', {}),
            'video': metadata.get('video', {})
        }

    except HttpError as error:
        return {'error': f'Failed to get media item: {error}'}

# ============================================================================
# MCP Server
# ============================================================================

app = Server(SERVER_NAME)

@app.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """List available Google resources"""
    return [
        {
            "uri": "gmail://inbox",
            "name": "Gmail Inbox",
            "description": "Recent emails from inbox",
            "mimeType": "application/json"
        },
        {
            "uri": "drive://files",
            "name": "Google Drive Files",
            "description": "Recent files in Google Drive",
            "mimeType": "application/json"
        },
        {
            "uri": "calendar://events",
            "name": "Calendar Events",
            "description": "Upcoming calendar events",
            "mimeType": "application/json"
        },
        {
            "uri": "photos://albums",
            "name": "Google Photos Albums",
            "description": "Photo albums in Google Photos",
            "mimeType": "application/json"
        },
        {
            "uri": "photos://recent",
            "name": "Recent Photos",
            "description": "Recently added photos",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a Google resource"""
    if uri == "gmail://inbox":
        messages = gmail_search(query='in:inbox', max_results=10)
        return json.dumps(messages, indent=2)

    elif uri == "drive://files":
        files = drive_list_files(max_results=20)
        return json.dumps(files, indent=2)

    elif uri == "calendar://events":
        events = calendar_list_events(max_results=10)
        return json.dumps(events, indent=2)

    elif uri == "photos://albums":
        albums = photos_list_albums(max_results=20)
        return json.dumps(albums, indent=2)

    elif uri == "photos://recent":
        photos = photos_search(max_results=20)
        return json.dumps(photos, indent=2)

    raise ValueError(f"Unknown resource: {uri}")

@app.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """List available Google tools"""
    return [
        # Gmail tools
        {
            "name": "gmail_search",
            "description": "Search Gmail messages with query",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:someone@email.com', 'subject:important')"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        },
        {
            "name": "gmail_send",
            "description": "Send an email via Gmail",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        },
        # Drive tools
        {
            "name": "drive_list_files",
            "description": "List files in Google Drive",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Drive API query (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of files (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        },
        {
            "name": "drive_search_files",
            "description": "Search for files by name in Google Drive",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "File name to search for"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "drive_get_file",
            "description": "Get file metadata and content (for text files)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "Google Drive file ID"
                    }
                },
                "required": ["file_id"]
            }
        },
        # Calendar tools
        {
            "name": "calendar_list_events",
            "description": "List upcoming calendar events",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of events (default: 10)",
                        "default": 10
                    },
                    "days_ahead": {
                        "type": "number",
                        "description": "Number of days to look ahead (default: 7)",
                        "default": 7
                    }
                },
                "required": []
            }
        },
        {
            "name": "calendar_create_event",
            "description": "Create a new calendar event",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title/summary"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time (ISO 8601 format, e.g., '2025-11-09T10:00:00Z')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time (ISO 8601 format)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description (optional)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location (optional)"
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        },
        # Photos tools
        {
            "name": "photos_list_albums",
            "description": "List photo albums in Google Photos",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of albums (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        },
        {
            "name": "photos_search",
            "description": "Search for photos, optionally in a specific album",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "album_id": {
                        "type": "string",
                        "description": "Album ID to search within (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of photos (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        },
        {
            "name": "photos_get_media",
            "description": "Get details of a specific photo or video",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "media_id": {
                        "type": "string",
                        "description": "Media item ID from Google Photos"
                    }
                },
                "required": ["media_id"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict[str, Any]]:
    """Execute a Google tool"""

    # Gmail tools
    if name == "gmail_search":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        result = gmail_search(query, max_results)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "gmail_send":
        result = gmail_send(
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"]
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Drive tools
    elif name == "drive_list_files":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 20)
        result = drive_list_files(query, max_results)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "drive_search_files":
        result = drive_search_files(arguments["name"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "drive_get_file":
        result = drive_get_file_content(arguments["file_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Calendar tools
    elif name == "calendar_list_events":
        max_results = arguments.get("max_results", 10)
        days_ahead = arguments.get("days_ahead", 7)
        result = calendar_list_events(max_results, days_ahead)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "calendar_create_event":
        result = calendar_create_event(
            summary=arguments["summary"],
            start_time=arguments["start_time"],
            end_time=arguments["end_time"],
            description=arguments.get("description", ""),
            location=arguments.get("location", "")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Photos tools
    elif name == "photos_list_albums":
        max_results = arguments.get("max_results", 20)
        result = photos_list_albums(max_results)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "photos_search":
        album_id = arguments.get("album_id")
        max_results = arguments.get("max_results", 20)
        result = photos_search(album_id, max_results)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "photos_get_media":
        result = photos_get_media_item(arguments["media_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    raise ValueError(f"Unknown tool: {name}")

# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the Google MCP server"""
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print("Authenticating with Google...")

    try:
        # Test authentication
        get_credentials()
        print("✓ Google authentication successful")
        print("Server is ready for connections...")

        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
