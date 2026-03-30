from __future__ import annotations

import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from queue import Queue
from azure.communication.email import EmailClient
from azure.core.exceptions import HttpResponseError

from app.config import settings


class EmailSender:
    def __init__(self) -> None:
        # Gmail SMTP takes priority if configured
        self.use_gmail = bool(settings.gmail_user and settings.gmail_app_password)

        if settings.acs_email_connection_string and settings.acs_email_sender:
            self.client = EmailClient.from_connection_string(settings.acs_email_connection_string)
        else:
            self.client = None
        
        # Queue for rate-limited email sending
        self.send_queue = Queue()
        self.worker_thread = None
        self._start_worker()

    def _start_worker(self):
        """Start background worker thread for processing email queue."""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()

    def _process_queue(self):
        """Process email queue with rate limiting to respect ACS quotas."""
        while True:
            try:
                item = self.send_queue.get(timeout=1)
                if item is None:  # Shutdown signal
                    break
                
                recipient, subject, body, callback = item
                try:
                    message = {
                        "senderAddress": settings.acs_email_sender,
                        "recipients": {"to": [{"address": recipient}]},
                        "content": {
                            "subject": subject,
                            "plainText": body,
                        },
                    }
                    poller = self.client.begin_send(message)
                    result = poller.result()
                    message_id = result.get("messageId", "sent")
                    if callback:
                        callback(True, message_id, None)
                except HttpResponseError as e:
                    if e.status_code == 429:
                        # Re-queue with exponential backoff
                        time.sleep(5)  # Wait 5s before retrying
                        self.send_queue.put(item)
                    else:
                        if callback:
                            callback(False, None, str(e))
                except Exception as e:
                    if callback:
                        callback(False, None, str(e))
                
                # Rate limit: 1 email per second
                time.sleep(1)
            except:
                continue

    def is_configured(self) -> bool:
        return self.use_gmail or bool(self.client and settings.acs_email_sender)

    def _send_via_gmail(self, recipient: str, subject: str, body: str) -> str:
        """Send immediately via Gmail SMTP."""
        msg = MIMEMultipart()
        msg["From"] = settings.gmail_user
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, recipient, msg.as_string())
        return "gmail_sent"

    def send(self, recipient: str, subject: str, body: str, callback=None) -> str:
        """Send via Gmail SMTP (preferred) or queue via ACS."""
        if not self.is_configured():
            raise RuntimeError("Email service not configured")

        if self.use_gmail:
            return self._send_via_gmail(recipient, subject, body)

        # Fall back to ACS queue
        self.send_queue.put((recipient, subject, body, callback))
        return "queued"


