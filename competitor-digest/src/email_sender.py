"""Email delivery via SMTP or Resend API."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str, *, html: bool = False) -> None:
    """
    Send email using SMTP or Resend API, depending on environment variables.
    """
    email_from = os.environ.get("EMAIL_FROM")
    email_to = os.environ.get("EMAIL_TO")

    if not email_from or not email_to:
        raise ValueError("EMAIL_FROM and EMAIL_TO environment variables are required")

    if os.environ.get("RESEND_API_KEY"):
        _send_via_resend(subject, body, email_from, email_to, html=html)
    else:
        _send_via_smtp(subject, body, email_from, email_to, html=html)


def _send_via_smtp(
    subject: str, body: str, email_from: str, email_to: str, *, html: bool = False
) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")

    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD are required for SMTP")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to

    part = MIMEText(body, "html" if html else "plain")
    msg.attach(part)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(email_from, email_to.split(","), msg.as_string())

    logger.info("Email sent via SMTP to %s", email_to)


def _send_via_resend(
    subject: str, body: str, email_from: str, email_to: str, *, html: bool = False
) -> None:
    import httpx

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise ValueError("RESEND_API_KEY is required for Resend")

    payload = {
        "from": email_from,
        "to": [addr.strip() for addr in email_to.split(",")],
        "subject": subject,
    }
    payload["html" if html else "text"] = body

    resp = httpx.post(
        "https://api.resend.com/emails",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    logger.info("Email sent via Resend to %s", email_to)
