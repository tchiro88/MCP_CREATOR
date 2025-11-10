"""
Priority Analyzer - Smart tool to create priority action lists
Analyzes emails and calendar to generate prioritized task recommendations
"""

from datetime import datetime, timedelta
from typing import List, Dict
import re


class PriorityAnalyzer:
    """Analyzes emails and calendar to create priority action lists"""

    # Keywords that indicate urgency
    URGENT_KEYWORDS = [
        'urgent', 'asap', 'immediately', 'critical', 'emergency',
        'today', 'deadline', 'due', 'time-sensitive', 'important'
    ]

    # Action keywords
    ACTION_KEYWORDS = [
        'please', 'need', 'required', 'must', 'should', 'action',
        'review', 'approve', 'sign', 'complete', 'finish', 'send',
        'respond', 'reply', 'feedback', 'decision', 'confirm'
    ]

    # Deadline patterns
    DEADLINE_PATTERNS = [
        r'by (\w+ \d+)',  # by Dec 15
        r'due (\w+)',  # due Friday
        r'deadline[:\s]+(\w+ \d+)',  # deadline: Dec 15
        r'before (\w+)',  # before Friday
        r'eod\s*(\w+)?',  # EOD or EOD Friday
    ]

    def __init__(self, email_reader, calendar_reader):
        self.email_reader = email_reader
        self.calendar_reader = calendar_reader

    def _score_urgency(self, email: Dict) -> int:
        """Score email urgency (0-100)"""
        score = 0

        subject = (email.get('subject', '') or '').lower()
        body = (email.get('body', '') or '').lower()
        from_addr = (email.get('from', '') or '').lower()

        # Check for urgent keywords
        for keyword in self.URGENT_KEYWORDS:
            if keyword in subject:
                score += 20
            if keyword in body:
                score += 10

        # Check for action keywords
        for keyword in self.ACTION_KEYWORDS:
            if keyword in subject:
                score += 15
            if keyword in body:
                score += 5

        # Check how recent
        try:
            email_date = datetime.fromisoformat(email.get('date', ''))
            hours_old = (datetime.now(email_date.tzinfo) - email_date).total_seconds() / 3600

            if hours_old < 1:
                score += 30  # Very recent
            elif hours_old < 6:
                score += 20
            elif hours_old < 24:
                score += 10
        except:
            pass

        # Boss/VIP detection (simple heuristic)
        vip_indicators = ['ceo', 'president', 'director', 'vp', 'chief']
        for indicator in vip_indicators:
            if indicator in from_addr:
                score += 25
                break

        return min(score, 100)

    def _extract_action_items(self, emails: List[Dict]) -> List[Dict]:
        """Extract action items from emails"""
        action_items = []

        for email in emails:
            score = self._score_urgency(email)

            # Only include emails with some urgency
            if score >= 20:
                # Try to extract deadline
                deadline = None
                body = email.get('body', '') or ''

                for pattern in self.DEADLINE_PATTERNS:
                    match = re.search(pattern, body, re.IGNORECASE)
                    if match:
                        deadline = match.group(0)
                        break

                action_items.append({
                    'email_id': email.get('id'),
                    'subject': email.get('subject', 'No Subject'),
                    'from': email.get('from', 'Unknown'),
                    'date': email.get('date', ''),
                    'urgency_score': score,
                    'priority': 'HIGH' if score >= 70 else 'MEDIUM' if score >= 40 else 'LOW',
                    'deadline': deadline,
                    'body_preview': (email.get('body', '') or '')[:150]
                })

        # Sort by urgency score
        action_items.sort(key=lambda x: x['urgency_score'], reverse=True)

        return action_items

    def _find_free_time_blocks(self, events: List[Dict], date: datetime) -> List[Dict]:
        """Find free time blocks in calendar"""
        # Work hours: 9 AM to 5 PM
        work_start = date.replace(hour=9, minute=0, second=0, microsecond=0)
        work_end = date.replace(hour=17, minute=0, second=0, microsecond=0)

        # Sort events by start time
        sorted_events = sorted(events, key=lambda x: x.get('start', ''))

        free_blocks = []
        current_time = work_start

        for event in sorted_events:
            try:
                event_start = datetime.fromisoformat(event.get('start', ''))
                event_end = datetime.fromisoformat(event.get('end', ''))

                # Make timezone-aware if needed
                if event_start.tzinfo and current_time.tzinfo is None:
                    current_time = current_time.replace(tzinfo=event_start.tzinfo)
                elif current_time.tzinfo and event_start.tzinfo is None:
                    event_start = event_start.replace(tzinfo=current_time.tzinfo)

                # If there's a gap before this event
                if current_time < event_start:
                    duration = (event_start - current_time).total_seconds() / 60

                    if duration >= 15:  # At least 15 minutes
                        free_blocks.append({
                            'start': current_time.strftime('%I:%M %p'),
                            'end': event_start.strftime('%I:%M %p'),
                            'duration_minutes': int(duration)
                        })

                # Move current time to end of this event
                if event_end > current_time:
                    current_time = event_end
            except:
                continue

        # Check end of day
        if work_end.tzinfo is None and current_time.tzinfo:
            work_end = work_end.replace(tzinfo=current_time.tzinfo)

        if current_time < work_end:
            duration = (work_end - current_time).total_seconds() / 60
            if duration >= 15:
                free_blocks.append({
                    'start': current_time.strftime('%I:%M %p'),
                    'end': work_end.strftime('%I:%M %p'),
                    'duration_minutes': int(duration)
                })

        return free_blocks

    def _assign_to_time_blocks(self, action_items: List[Dict], free_blocks: List[Dict]) -> List[Dict]:
        """Assign action items to available time blocks"""
        # Estimate time for each action (simple heuristic)
        for item in action_items:
            if item['priority'] == 'HIGH':
                item['estimated_minutes'] = 30
            elif item['priority'] == 'MEDIUM':
                item['estimated_minutes'] = 20
            else:
                item['estimated_minutes'] = 15

        # Assign to blocks
        scheduled = []
        remaining = []

        for item in action_items:
            assigned = False
            for block in free_blocks:
                if block['duration_minutes'] >= item['estimated_minutes']:
                    scheduled.append({
                        **item,
                        'suggested_time': f"{block['start']}-{block['end']}",
                        'time_block_duration': block['duration_minutes']
                    })
                    # Reduce block duration
                    block['duration_minutes'] -= item['estimated_minutes']
                    assigned = True
                    break

            if not assigned:
                remaining.append(item)

        return scheduled, remaining

    def generate_priority_list(self, date: datetime = None) -> Dict:
        """
        Generate comprehensive priority action list

        Returns structured list with:
        - High priority items (scheduled to specific time blocks)
        - Medium priority items
        - Low priority items
        - Today's calendar
        - Available time blocks
        """
        if date is None:
            date = datetime.now()

        try:
            # Get unread emails
            emails = self.email_reader.get_unread_emails(limit=100)

            # Extract action items
            action_items = self._extract_action_items(emails)

            # Get today's calendar
            if date.date() == datetime.now().date():
                events = self.calendar_reader.get_today_events()
            else:
                start = date.replace(hour=0, minute=0, second=0)
                end = date.replace(hour=23, minute=59, second=59)
                events = self.calendar_reader.get_events_range(start, end)

            # Find free time blocks
            free_blocks = self._find_free_time_blocks(events, date)

            # Assign high priority items to time blocks
            high_priority = [i for i in action_items if i['priority'] == 'HIGH']
            medium_priority = [i for i in action_items if i['priority'] == 'MEDIUM']
            low_priority = [i for i in action_items if i['priority'] == 'LOW']

            scheduled, unscheduled_high = self._assign_to_time_blocks(high_priority, free_blocks.copy())

            # Calculate stats
            total_free_minutes = sum(b['duration_minutes'] for b in free_blocks)
            total_meetings = len(events)
            total_actions = len(action_items)

            return {
                'date': date.date().isoformat(),
                'summary': {
                    'total_action_items': total_actions,
                    'high_priority': len(high_priority),
                    'medium_priority': len(medium_priority),
                    'low_priority': len(low_priority),
                    'total_meetings': total_meetings,
                    'total_free_minutes': total_free_minutes
                },
                'high_priority_scheduled': scheduled,
                'high_priority_unscheduled': unscheduled_high,
                'medium_priority': medium_priority[:10],  # Top 10
                'low_priority': low_priority[:5],  # Top 5
                'meetings_today': events,
                'available_time_blocks': free_blocks
            }

        except Exception as e:
            raise Exception(f"Error generating priority list: {str(e)}")

    def daily_briefing(self) -> Dict:
        """Generate morning briefing"""
        try:
            priority_list = self.generate_priority_list()

            # Get today's critical info
            unread_count = self.email_reader.count_unread()

            briefing = {
                'date': datetime.now().date().isoformat(),
                'greeting': f"Good {'morning' if datetime.now().hour < 12 else 'afternoon'}!",
                'unread_emails': unread_count,
                'urgent_actions': len(priority_list['high_priority_scheduled']) + len(priority_list['high_priority_unscheduled']),
                'meetings_today': priority_list['summary']['total_meetings'],
                'available_time': f"{priority_list['summary']['total_free_minutes']} minutes",
                'top_priorities': priority_list['high_priority_scheduled'][:5],
                'calendar_summary': priority_list['meetings_today'],
                'recommendation': self._generate_recommendation(priority_list)
            }

            return briefing

        except Exception as e:
            raise Exception(f"Error generating daily briefing: {str(e)}")

    def _generate_recommendation(self, priority_list: Dict) -> str:
        """Generate smart recommendation"""
        free_minutes = priority_list['summary']['total_free_minutes']
        high_priority_count = priority_list['summary']['high_priority']
        meetings = priority_list['summary']['total_meetings']

        if meetings >= 5:
            return "Heavy meeting day. Try to tackle high-priority items in morning before meetings start."
        elif free_minutes >= 240:  # 4+ hours
            return "Good amount of free time today. Ideal for deep work on high-priority items."
        elif high_priority_count >= 5:
            return "Multiple urgent items. Consider blocking time for focused work."
        elif free_minutes < 60:
            return "Very limited free time. Focus on most critical items only."
        else:
            return "Balanced day. Tackle high-priority items between meetings."

    def analyze_workload(self, days: int = 7) -> Dict:
        """Analyze workload over multiple days"""
        try:
            # Get emails from last N days
            emails = self.email_reader.get_recent_emails(days=days, limit=500)

            # Get calendar for next N days
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            events = self.calendar_reader.get_events_range(start_date, end_date)

            # Calculate stats
            emails_per_day = len(emails) / days
            meetings_per_day = len(events) / days

            # Group by day
            daily_stats = {}

            return {
                'period': f"{days} days",
                'total_emails': len(emails),
                'avg_emails_per_day': round(emails_per_day, 1),
                'total_meetings': len(events),
                'avg_meetings_per_day': round(meetings_per_day, 1),
                'unread_count': self.email_reader.count_unread(),
                'recommendation': f"{'High' if emails_per_day > 50 else 'Moderate'} email volume. " +
                                f"{'Heavy' if meetings_per_day > 4 else 'Normal'} meeting load."
            }

        except Exception as e:
            raise Exception(f"Error analyzing workload: {str(e)}")
