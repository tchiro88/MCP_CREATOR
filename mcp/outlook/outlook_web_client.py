"""
Outlook Web Client using Playwright for browser automation.

This module provides an async interface to interact with Outlook.com
through browser automation, handling authentication, session management,
and data extraction.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class OutlookSessionError(Exception):
    """Raised when session is invalid or expired."""
    pass


class OutlookLoginRequiredError(OutlookSessionError):
    """Raised when user needs to perform interactive login."""
    pass


class OutlookWebClient:
    """
    Async Playwright-based client for automating Outlook.com.

    Handles session persistence, authentication state, and data extraction
    from the Outlook web interface using async/await patterns.

    Attributes:
        session_dir: Directory to store session state
        headless: Whether to run browser in headless mode
        timeout: Default timeout in milliseconds
    """

    def __init__(
        self,
        email: str,
        password: str,
        session_dir: str = "/app/session",
        headless: bool = True,
        timeout: int = 30000
    ) -> None:
        """
        Initialize the Outlook web client.

        Args:
            email: Outlook email address
            password: Outlook password
            session_dir: Directory to store session state (default: /app/session)
            headless: Whether to run browser in headless mode (default: True)
            timeout: Default timeout in milliseconds (default: 30000)
        """
        self.email = email
        self.password = password
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / "outlook_state.json"
        self.headless = headless
        self.timeout = timeout

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._logged_in = False

    async def _start_browser(self) -> None:
        """Start the Playwright browser and context."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        if self.browser is None:
            logger.info(f"Starting browser (headless={self.headless})")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )

    async def load_session(self) -> bool:
        """
        Load saved browser session if it exists.

        Returns:
            True if session loaded successfully, False otherwise
        """
        if not self.session_file.exists():
            logger.info("No saved session found")
            return False

        try:
            logger.info("Loading saved session")
            await self._start_browser()

            # Load the saved context state
            self.context = await self.browser.new_context(
                storage_state=str(self.session_file),
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)

            # Verify session is valid by navigating to Outlook
            logger.info("Verifying session validity")
            await self.page.goto("https://outlook.office.com/mail/", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3000)

            # Check if we're logged in by looking for mail interface
            if await self._is_logged_in():
                logger.info("Session loaded and validated successfully")
                self._logged_in = True
                return True
            else:
                logger.warning("Session loaded but appears invalid")
                await self._cleanup_context()
                return False

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            await self._cleanup_context()
            return False

    async def _is_logged_in(self) -> bool:
        """
        Check if currently logged into Outlook.

        Returns:
            True if logged in, False otherwise
        """
        try:
            if not self.page:
                return False

            # Check for common Outlook UI elements
            # Look for mail folder list or inbox
            selectors = [
                '[aria-label*="Folder list"]',
                '[aria-label*="Message list"]',
                '[data-app-section="MailCompose"]',
                'div[role="main"]'
            ]

            for selector in selectors:
                if await self.page.locator(selector).count() > 0:
                    return True

            # If we see login button, definitely not logged in
            if await self.page.locator('a:has-text("Sign in")').count() > 0:
                return False

            return False

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    async def save_session(self) -> None:
        """Save current browser session state."""
        try:
            if self.context:
                logger.info("Saving session state")
                await self.context.storage_state(path=str(self.session_file))
                logger.info(f"Session saved to {self.session_file}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def _cleanup_context(self) -> None:
        """Clean up browser context and page."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def login(self) -> bool:
        """
        Perform headless login and save session.

        Attempts to login using stored email/password credentials and saves
        the session for future use.

        Returns:
            True if login successful, False otherwise

        Raises:
            OutlookSessionError: If login fails due to credentials or network
        """
        try:
            logger.info(f"Attempting login for {self.email}")
            await self._start_browser()

            # Create new context for login
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)

            # Navigate to Outlook login
            logger.info("Navigating to Outlook login page")
            await self.page.goto("https://outlook.office.com/mail/")
            await self.page.wait_for_timeout(2000)

            # Fill email
            logger.info("Entering email")
            email_input = self.page.locator('input[type="email"], input[name="loginfmt"], input[placeholder*="email"]').first
            await email_input.fill(self.email)
            await self.page.wait_for_timeout(500)

            # Click Next
            next_button = self.page.locator('button:has-text("Next"), input[type="submit"]').first
            await next_button.click()
            await self.page.wait_for_timeout(2000)

            # Fill password
            logger.info("Entering password")
            password_input = self.page.locator('input[type="password"], input[name="passwd"]').first
            await password_input.fill(self.password)
            await self.page.wait_for_timeout(500)

            # Click Sign in
            signin_button = self.page.locator('button:has-text("Sign in"), input[type="submit"]').first
            await signin_button.click()

            # Wait for mail interface or handle MFA
            logger.info("Waiting for login completion")
            try:
                await self.page.wait_for_selector(
                    '[aria-label*="Folder list"], [aria-label*="Message list"], [data-app-section="MailCompose"]',
                    timeout=30000
                )
            except PlaywrightTimeoutError:
                logger.error("Login timeout - may require manual MFA completion")
                return False

            # Verify login success
            if await self._is_logged_in():
                logger.info("Login successful!")
                await self.save_session()
                self._logged_in = True
                return True
            else:
                logger.error("Login verification failed")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            raise OutlookSessionError(f"Failed to login: {str(e)}")

    async def is_session_valid(self) -> bool:
        """
        Check if current session is valid and logged in.

        Returns:
            True if session exists and is valid, False otherwise
        """
        if self._logged_in:
            return True

        return await self.load_session()

    async def get_unread_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of unread emails from inbox.

        Args:
            limit: Maximum number of emails to return

        Returns:
            List of email dictionaries with id, subject, sender, date
        """
        try:
            if not await self.is_session_valid():
                raise OutlookLoginRequiredError(
                    "No valid session found. Please call login() first."
                )

            logger.info(f"Fetching up to {limit} unread emails")

            # Navigate to inbox if not already there
            await self.page.goto("https://outlook.office.com/mail/inbox", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)

            # Wait for message list to load
            try:
                await self.page.wait_for_selector('[role="listbox"], [role="list"]', timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning("Message list did not load in time")
                return []

            emails = []

            # Find unread messages
            # Outlook marks unread with specific attributes
            message_items = await self.page.locator('[role="listitem"][aria-label*="Unread"]').all()
            message_items = message_items[:limit]

            for idx, item in enumerate(message_items):
                try:
                    # Extract email data from the list item
                    aria_label = await item.get_attribute("aria-label") or ""

                    # Try to extract structured data
                    email_data = {
                        "id": f"email_{idx}_{datetime.now().timestamp()}",
                        "subject": "",
                        "sender": "",
                        "preview": "",
                        "date": "",
                        "unread": True
                    }

                    # Parse aria-label which often contains: "Unread, From: X, Subject: Y, Received: Z"
                    parts = aria_label.split(", ")
                    for part in parts:
                        if part.startswith("From:"):
                            email_data["sender"] = part.replace("From:", "").strip()
                        elif part.startswith("Subject:"):
                            email_data["subject"] = part.replace("Subject:", "").strip()
                        elif "Received:" in part:
                            email_data["date"] = part.split("Received:")[-1].strip()

                    # If aria-label parsing didn't work, try text content
                    if not email_data["subject"]:
                        text = await item.inner_text()
                        lines = text.split("\n")
                        if len(lines) >= 2:
                            email_data["sender"] = lines[0]
                            email_data["subject"] = lines[1]
                            if len(lines) > 2:
                                email_data["preview"] = lines[2]

                    emails.append(email_data)

                except Exception as e:
                    logger.warning(f"Failed to parse email item {idx}: {e}")
                    continue

            logger.info(f"Retrieved {len(emails)} unread emails")
            return emails

        except OutlookLoginRequiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to get unread emails: {e}")
            raise Exception(f"Failed to retrieve unread emails: {str(e)}")

    async def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """
        Get full email content by email ID.

        Note: Since email_id is generated from list, this retrieves the first
        unread email or searches by subject in production scenarios.

        Args:
            email_id: Email identifier

        Returns:
            Dictionary with full email content including body
        """
        try:
            if not await self.is_session_valid():
                raise OutlookLoginRequiredError(
                    "No valid session found. Please call login() first."
                )

            logger.info(f"Reading email: {email_id}")

            # Navigate to inbox
            await self.page.goto("https://outlook.office.com/mail/inbox", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)

            # Get first email (simplified approach)
            # In production, you'd map email_id to actual email location
            try:
                await self.page.wait_for_selector('[role="listitem"]', timeout=5000)
            except PlaywrightTimeoutError:
                logger.warning("No emails found")
                return {"id": email_id, "error": "No emails found"}

            # Click first email to open it
            first_email = self.page.locator('[role="listitem"]').first
            await first_email.click()
            await self.page.wait_for_timeout(2000)

            # Extract email content
            email_data = {
                "id": email_id,
                "subject": "",
                "sender": "",
                "to": "",
                "date": "",
                "body": ""
            }

            # Try to get subject from header
            try:
                subject_elem = self.page.locator('[data-testid*="subject"], [role="heading"]').first
                email_data["subject"] = await subject_elem.inner_text()
            except:
                pass

            # Try to get sender
            try:
                sender_elem = self.page.locator('[aria-label*="From:"], .ms-font-m').first
                email_data["sender"] = await sender_elem.inner_text()
            except:
                pass

            # Try to get body
            try:
                body_elem = self.page.locator('[role="article"], .ms-font-m[dir="auto"]').first
                email_data["body"] = await body_elem.inner_text()
            except:
                pass

            logger.info(f"Retrieved email content for {email_id}")
            return email_data

        except OutlookLoginRequiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to read email: {e}")
            raise Exception(f"Failed to read email: {str(e)}")

    def search_emails(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search emails by query.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching emails
        """
        try:
            self._ensure_session()
            logger.info(f"Searching emails for: {query}")

            # Navigate to mail
            self.page.goto("https://outlook.office.com/mail/inbox", wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

            # Find and use search box
            search_box = self.page.locator('[aria-label*="Search"], [placeholder*="Search"]').first
            search_box.click()
            search_box.fill(query)
            search_box.press("Enter")

            # Wait for results
            self.page.wait_for_timeout(3000)

            # Parse results (similar to unread emails)
            emails = []
            message_items = self.page.locator('[role="listitem"]').all()[:limit]

            for idx, item in enumerate(message_items):
                try:
                    aria_label = item.get_attribute("aria-label") or ""
                    text = item.inner_text()

                    email_data = {
                        "id": f"search_{idx}_{datetime.now().timestamp()}",
                        "subject": "",
                        "sender": "",
                        "preview": text[:200] if text else "",
                        "date": ""
                    }

                    lines = text.split("\n")
                    if len(lines) >= 2:
                        email_data["sender"] = lines[0]
                        email_data["subject"] = lines[1]

                    emails.append(email_data)

                except Exception as e:
                    logger.warning(f"Failed to parse search result {idx}: {e}")
                    continue

            logger.info(f"Found {len(emails)} emails matching query")
            return emails

        except OutlookLoginRequiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to search emails: {e}")
            raise Exception(f"Failed to search emails: {str(e)}")

    def get_calendar_events_today(self) -> List[Dict[str, Any]]:
        """
        Get today's calendar events.

        Returns:
            List of event dictionaries
        """
        try:
            self._ensure_session()
            logger.info("Fetching today's calendar events")

            # Navigate to calendar
            self.page.goto("https://outlook.office.com/calendar/view/day", wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)

            # Wait for calendar to load
            self.page.wait_for_selector('[role="main"], [data-app-section="Calendar"]', timeout=10000)

            events = []

            # Find event elements
            event_items = self.page.locator('[role="button"][aria-label*="event"], [data-is-focusable="true"][aria-label*=","]').all()

            for idx, item in enumerate(event_items):
                try:
                    aria_label = item.get_attribute("aria-label") or ""

                    event_data = {
                        "id": f"event_{idx}_{datetime.now().timestamp()}",
                        "title": "",
                        "time": "",
                        "location": "",
                        "details": aria_label
                    }

                    # Parse aria-label which often contains time and title
                    if "," in aria_label:
                        parts = aria_label.split(",", 1)
                        event_data["time"] = parts[0].strip()
                        event_data["title"] = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        event_data["title"] = aria_label

                    events.append(event_data)

                except Exception as e:
                    logger.warning(f"Failed to parse event {idx}: {e}")
                    continue

            logger.info(f"Retrieved {len(events)} events for today")
            return events

        except OutlookLoginRequiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            raise Exception(f"Failed to retrieve calendar events: {str(e)}")

    def get_calendar_events_week(self) -> List[Dict[str, Any]]:
        """
        Get this week's calendar events.

        Returns:
            List of event dictionaries
        """
        try:
            self._ensure_session()
            logger.info("Fetching this week's calendar events")

            # Navigate to calendar week view
            self.page.goto("https://outlook.office.com/calendar/view/week", wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)

            # Wait for calendar to load
            self.page.wait_for_selector('[role="main"], [data-app-section="Calendar"]', timeout=10000)

            events = []

            # Find event elements
            event_items = self.page.locator('[role="button"][aria-label*="event"], [data-is-focusable="true"][aria-label*=","]').all()

            for idx, item in enumerate(event_items):
                try:
                    aria_label = item.get_attribute("aria-label") or ""

                    event_data = {
                        "id": f"event_week_{idx}_{datetime.now().timestamp()}",
                        "title": "",
                        "time": "",
                        "location": "",
                        "details": aria_label
                    }

                    # Parse event data
                    if "," in aria_label:
                        parts = aria_label.split(",")
                        if len(parts) >= 2:
                            event_data["time"] = parts[0].strip()
                            event_data["title"] = parts[1].strip()
                            if len(parts) > 2:
                                event_data["location"] = parts[2].strip()
                    else:
                        event_data["title"] = aria_label

                    events.append(event_data)

                except Exception as e:
                    logger.warning(f"Failed to parse event {idx}: {e}")
                    continue

            logger.info(f"Retrieved {len(events)} events for the week")
            return events

        except OutlookLoginRequiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            raise Exception(f"Failed to retrieve calendar events: {str(e)}")

    def close(self) -> None:
        """Clean up and close browser resources."""
        logger.info("Closing Outlook client")
        try:
            self._cleanup_context()
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception as e:
            logger.error(f"Error during close: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
