"""
Outlook Email Reader (Read-Only)
Uses IMAP to read emails from Outlook/Office 365
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional


class OutlookEmailReader:
    """Read-only email client for Outlook via IMAP"""

    def __init__(self, email_address: str, password: str):
        self.email_address = email_address
        self.password = password
        self.imap = None

    def connect(self):
        """Connect to Outlook IMAP server"""
        try:
            self.imap = imaplib.IMAP4_SSL('outlook.office365.com', 993)
            self.imap.login(self.email_address, self.password)
            return True
        except Exception as e:
            raise Exception(f"Failed to connect to Outlook IMAP: {str(e)}")

    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass

    def _decode_header(self, header):
        """Decode email header"""
        if header is None:
            return ""

        decoded = decode_header(header)
        header_parts = []

        for content, encoding in decoded:
            if isinstance(content, bytes):
                try:
                    header_parts.append(content.decode(encoding or 'utf-8'))
                except:
                    header_parts.append(content.decode('utf-8', errors='ignore'))
            else:
                header_parts.append(str(content))

        return ''.join(header_parts)

    def _parse_email(self, email_data) -> Dict:
        """Parse email data into structured format"""
        msg = email.message_from_bytes(email_data[0][1])

        # Extract basic info
        subject = self._decode_header(msg.get('Subject', ''))
        from_addr = self._decode_header(msg.get('From', ''))
        to_addr = self._decode_header(msg.get('To', ''))
        date_str = msg.get('Date', '')

        # Parse date
        try:
            date = email.utils.parsedate_to_datetime(date_str)
        except:
            date = datetime.now()

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())

        # Extract attachments info
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': self._decode_header(filename),
                            'size': len(part.get_payload(decode=True) or b'')
                        })

        return {
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date.isoformat() if date else '',
            'body': body[:500],  # First 500 chars
            'body_full': body,
            'has_attachments': len(attachments) > 0,
            'attachments': attachments
        }

    def get_unread_emails(self, limit: int = 50) -> List[Dict]:
        """Get unread emails"""
        if not self.imap:
            self.connect()

        self.imap.select('INBOX')
        _, messages = self.imap.search(None, 'UNSEEN')

        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]  # Get last N

        emails = []
        for email_id in reversed(email_ids):  # Most recent first
            try:
                _, msg_data = self.imap.fetch(email_id, '(RFC822)')
                parsed = self._parse_email(msg_data)
                parsed['id'] = email_id.decode()
                emails.append(parsed)
            except Exception as e:
                print(f"Error parsing email {email_id}: {e}")

        return emails

    def get_recent_emails(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """Get emails from last N days"""
        if not self.imap:
            self.connect()

        self.imap.select('INBOX')

        # Calculate date
        since_date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
        _, messages = self.imap.search(None, f'SINCE {since_date}')

        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]  # Get last N

        emails = []
        for email_id in reversed(email_ids):
            try:
                _, msg_data = self.imap.fetch(email_id, '(RFC822)')
                parsed = self._parse_email(msg_data)
                parsed['id'] = email_id.decode()
                emails.append(parsed)
            except Exception as e:
                print(f"Error parsing email {email_id}: {e}")

        return emails

    def search_emails(self, query: str, days: int = 30) -> List[Dict]:
        """Search emails by subject or body"""
        if not self.imap:
            self.connect()

        self.imap.select('INBOX')

        # Search by subject
        _, messages = self.imap.search(None, f'SUBJECT "{query}"')
        email_ids = messages[0].split()

        # Also search by body (if not too many results)
        if len(email_ids) < 50:
            _, body_messages = self.imap.search(None, f'BODY "{query}"')
            body_ids = body_messages[0].split()
            # Combine and deduplicate
            email_ids = list(set(email_ids + body_ids))

        # Filter by date
        since_date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
        _, date_messages = self.imap.search(None, f'SINCE {since_date}')
        date_ids = set(date_messages[0].split())

        # Intersect with date filter
        email_ids = [eid for eid in email_ids if eid in date_ids]

        emails = []
        for email_id in reversed(email_ids[-50:]):  # Last 50 matches
            try:
                _, msg_data = self.imap.fetch(email_id, '(RFC822)')
                parsed = self._parse_email(msg_data)
                parsed['id'] = email_id.decode()
                emails.append(parsed)
            except Exception as e:
                print(f"Error parsing email {email_id}: {e}")

        return emails

    def get_email_by_id(self, email_id: str) -> Optional[Dict]:
        """Get full email by ID"""
        if not self.imap:
            self.connect()

        self.imap.select('INBOX')

        try:
            _, msg_data = self.imap.fetch(email_id.encode(), '(RFC822)')
            parsed = self._parse_email(msg_data)
            parsed['id'] = email_id
            return parsed
        except:
            return None

    def count_unread(self) -> int:
        """Count unread emails"""
        if not self.imap:
            self.connect()

        self.imap.select('INBOX')
        _, messages = self.imap.search(None, 'UNSEEN')
        return len(messages[0].split())
