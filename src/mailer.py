"""Send the brief via Gmail SMTP (free, no domain needed, works with an App Password)."""
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from .config import Config

BRIEF_HEADER = "X-Daily-Teardown"  # lets the capture loop tell our own emails apart from your replies


def send(cfg: Config, *, subject: str, html: str, text: str) -> str:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg.podcast_title, cfg.gmail_address))
    msg["To"] = cfg.recipient
    msg["Reply-To"] = cfg.gmail_address
    msg["Message-ID"] = make_msgid(domain="daily-teardown")
    msg[BRIEF_HEADER] = "brief"
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(cfg.gmail_address, cfg.gmail_app_password.replace(" ", ""))
        s.send_message(msg)
    print(f"[mail] sent to {cfg.recipient}: {subject}", file=sys.stderr)
    return msg["Message-ID"]
