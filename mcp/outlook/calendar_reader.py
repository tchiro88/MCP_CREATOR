"""
Outlook Calendar Reader (Read-Only)
Uses Exchange Web Services (EWS) to read calendar events
"""

from exchangelib import Credentials, Account, Configuration, DELEGATE
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional


# Disable SSL warnings for self-signed certs (if needed)
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter


class OutlookCalendarReader:
    """Read-only calendar client for Outlook via EWS"""

    def __init__(self, email_address: str, password: str):
        self.email_address = email_address
        self.password = password
        self.account = None

    def connect(self):
        """Connect to Outlook/Exchange"""
        try:
            credentials = Credentials(self.email_address, self.password)

            # Try with autodiscover first
            try:
                self.account = Account(
                    self.email_address,
                    credentials=credentials,
                    autodiscover=True,
                    access_type=DELEGATE
                )
            except:
                # Fallback to manual configuration
                config = Configuration(
                    server='outlook.office365.com',
                    credentials=credentials
                )
                self.account = Account(
                    primary_smtp_address=self.email_address,
                    config=config,
                    autodiscover=False,
                    access_type=DELEGATE
                )

            return True
        except Exception as e:
            raise Exception(f"Failed to connect to Outlook calendar: {str(e)}")

    def _parse_event(self, item) -> Dict:
        """Parse calendar event into structured format"""
        try:
            return {
                'id': item.id if hasattr(item, 'id') else '',
                'subject': item.subject or 'No Subject',
                'start': item.start.isoformat() if item.start else '',
                'end': item.end.isoformat() if item.end else '',
                'location': item.location or '',
                'organizer': str(item.organizer) if hasattr(item, 'organizer') and item.organizer else '',
                'attendees': [str(att) for att in (item.required_attendees or [])][:10],  # Max 10
                'body': (item.text_body or '')[:200],  # First 200 chars
                'is_all_day': getattr(item, 'is_all_day_event', False),
                'is_meeting': bool(item.required_attendees) if hasattr(item, 'required_attendees') else False,
                'status': item.my_response_type if hasattr(item, 'my_response_type') else 'Unknown'
            }
        except Exception as e:
            return {
                'subject': 'Error parsing event',
                'error': str(e)
            }

    def get_today_events(self) -> List[Dict]:
        """Get today's calendar events"""
        if not self.account:
            self.connect()

        # Get today's date range
        tz = self.account.default_timezone
        now = tz.localize(datetime.now())
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            events = []
            for item in self.account.calendar.view(start=start_of_day, end=end_of_day):
                events.append(self._parse_event(item))

            # Sort by start time
            events.sort(key=lambda x: x.get('start', ''))
            return events
        except Exception as e:
            raise Exception(f"Error fetching today's events: {str(e)}")

    def get_week_events(self) -> List[Dict]:
        """Get this week's calendar events"""
        if not self.account:
            self.connect()

        # Get this week's date range
        tz = self.account.default_timezone
        now = tz.localize(datetime.now())
        start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = (start_of_week + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            events = []
            for item in self.account.calendar.view(start=start_of_week, end=end_of_week):
                events.append(self._parse_event(item))

            # Sort by start time
            events.sort(key=lambda x: x.get('start', ''))
            return events
        except Exception as e:
            raise Exception(f"Error fetching week events: {str(e)}")

    def get_events_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get events in a date range"""
        if not self.account:
            self.connect()

        tz = self.account.default_timezone

        # Localize dates if not already
        if start_date.tzinfo is None:
            start_date = tz.localize(start_date)
        if end_date.tzinfo is None:
            end_date = tz.localize(end_date)

        try:
            events = []
            for item in self.account.calendar.view(start=start_date, end=end_date):
                events.append(self._parse_event(item))

            # Sort by start time
            events.sort(key=lambda x: x.get('start', ''))
            return events
        except Exception as e:
            raise Exception(f"Error fetching events in range: {str(e)}")

    def search_events(self, query: str, days: int = 30) -> List[Dict]:
        """Search events by subject"""
        if not self.account:
            self.connect()

        # Get date range
        tz = self.account.default_timezone
        now = tz.localize(datetime.now())
        start_date = now - timedelta(days=days)
        end_date = now + timedelta(days=days)

        try:
            events = []
            for item in self.account.calendar.view(start=start_date, end=end_date):
                if query.lower() in (item.subject or '').lower():
                    events.append(self._parse_event(item))

            # Sort by start time
            events.sort(key=lambda x: x.get('start', ''))
            return events
        except Exception as e:
            raise Exception(f"Error searching events: {str(e)}")

    def check_availability(self, date: Optional[datetime] = None) -> Dict:
        """Check availability for a given day (default today)"""
        if not self.account:
            self.connect()

        if date is None:
            date = datetime.now()

        tz = self.account.default_timezone
        if date.tzinfo is None:
            date = tz.localize(date)

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            events = []
            for item in self.account.calendar.view(start=start_of_day, end=end_of_day):
                events.append({
                    'start': item.start.isoformat(),
                    'end': item.end.isoformat(),
                    'subject': item.subject or 'Busy'
                })

            # Calculate free time blocks
            events.sort(key=lambda x: x['start'])

            free_blocks = []
            work_start = start_of_day.replace(hour=9)  # 9 AM
            work_end = start_of_day.replace(hour=17)  # 5 PM

            current_time = work_start

            for event in events:
                event_start = datetime.fromisoformat(event['start'])
                event_end = datetime.fromisoformat(event['end'])

                # If there's a gap before this event
                if current_time < event_start and event_start <= work_end:
                    free_blocks.append({
                        'start': current_time.isoformat(),
                        'end': event_start.isoformat(),
                        'duration_minutes': int((event_start - current_time).total_seconds() / 60)
                    })

                # Move current time to end of this event
                if event_end > current_time:
                    current_time = event_end

            # Check if there's free time at the end of the day
            if current_time < work_end:
                free_blocks.append({
                    'start': current_time.isoformat(),
                    'end': work_end.isoformat(),
                    'duration_minutes': int((work_end - current_time).total_seconds() / 60)
                })

            return {
                'date': date.date().isoformat(),
                'total_meetings': len(events),
                'busy_blocks': events,
                'free_blocks': free_blocks,
                'total_free_minutes': sum(b['duration_minutes'] for b in free_blocks)
            }
        except Exception as e:
            raise Exception(f"Error checking availability: {str(e)}")
