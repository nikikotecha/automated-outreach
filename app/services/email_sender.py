from __future__ import annotations

from azure.communication.email import EmailClient

from app.config import settings


class EmailSender:
    def __init__(self) -> None:
        if settings.acs_email_connection_string and settings.acs_email_sender:
            self.client = EmailClient.from_connection_string(settings.acs_email_connection_string)
        else:
            self.client = None

    def is_configured(self) -> bool:
        return bool(self.client and settings.acs_email_sender)

    def send(self, recipient: str, subject: str, body: str) -> str:
        if not self.client or not settings.acs_email_sender:
            raise RuntimeError("Email service not configured")
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
        return result.get("messageId", "sent")
