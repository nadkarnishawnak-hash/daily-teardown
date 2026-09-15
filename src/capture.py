"""Capture loop: reply to any brief with a business name or link and it gets queued.

Reads the sending Gmail inbox over IMAP (same App Password as SMTP), looks for unread replies from you,
extracts the text you typed above the quoted brief, and marks the message read so it is never re-queued.
"""
import email
import imaplib
import re
import sys
from datetime import datetime, timezone
from email.header import decode_header, make_header
from html import unescape

from .config import Config
from .mailer import BRIEF_HEADER

QUOTE_MARKERS = re.compile(r"^(>|On .+wrote:|-{3,} ?Original Message|From: .+@)", re.I)


def _text_of(msg) -> str:
    plain, html = None, None
    for part in msg.walk():
        ctype = part.get_content_type()
        if part.get_content_disposition() == "attachment":
            continue
        try:
            payload = part.get_payload(decode=True)
        except Exception:
            continue
        if payload is None:
            continue
        body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain" and plain is None:
            plain = body
        elif ctype == "text/html" and html is None:
            html = body
    if plain is not None:
        return plain
    if html is not None:
        html = re.sub(r"<(br|/p|/div)[^>]*>", "\n", html, flags=re.I)
        return unescape(re.sub(r"<[^>]+>", "", html))
    return ""


def _typed_part(body: str) -> str:
    """Everything above the quoted brief, collapsed to a single request string."""
    lines = []
    for raw in body.replace("\r", "").split("\n"):
        line = raw.strip()
        if QUOTE_MARKERS.match(line):
            break
        if line:
            lines.append(line)
    return " ".join(lines).strip()


def fetch_requests(cfg: Config) -> list[dict]:
    if not cfg.can_email():
        return []
    found = []
    try:
        box = imaplib.IMAP4_SSL("imap.gmail.com")
        box.login(cfg.gmail_address, cfg.gmail_app_password.replace(" ", ""))
        box.select("INBOX")
        typ, data = box.search(None, "UNSEEN", "FROM", f'"{cfg.recipient}"')
        ids = data[0].split() if typ == "OK" and data and data[0] else []
        for num in ids:
            typ, parts = box.fetch(num, "(BODY.PEEK[])")
            if typ != "OK":
                continue
            msg = email.message_from_bytes(parts[0][1])
            if msg.get(BRIEF_HEADER):
                continue  # one of our own briefs (you send to yourself), not a reply
            subject = str(make_header(decode_header(msg.get("Subject", ""))))
            is_reply = bool(msg.get("In-Reply-To") or msg.get("References") or subject.lower().startswith("re:"))
            if not is_reply:
                continue
            request = _typed_part(_text_of(msg))
            box.store(num, "+FLAGS", "\\Seen")  # never process this message again
            if 2 <= len(request) <= 400:
                found.append({"request": request, "received": datetime.now(timezone.utc).isoformat(),
                              "subject": subject, "message_id": msg.get("Message-ID", "")})
                print(f"[capture] queued: {request!r}", file=sys.stderr)
        box.logout()
    except Exception as e:  # never let the capture loop block the edition
        print(f"[capture] failed: {e}", file=sys.stderr)
    return found
