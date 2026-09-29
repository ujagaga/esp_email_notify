import base64
import json
import os.path
from email.message import EmailMessage

import requests

from config import SENDERS
from gmail_auth import get_access_token

GMAIL_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
SENDERS_FILE = os.path.join(os.path.dirname(__file__), "senders.json")
RESPONSES_FILE = os.path.join(os.path.dirname(__file__), "responses.json")
NOTIFIED_FILE = os.path.join(os.path.dirname(__file__), "notified.json")  # message ids the ESP was last told about


def _load(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_senders():
    return _load(SENDERS_FILE, SENDERS)


def save_senders(senders):
    _save(SENDERS_FILE, senders)


def get_responses():
    return _load(RESPONSES_FILE, [])


def save_responses(responses):
    _save(RESPONSES_FILE, responses)


def get_notified():
    return _load(NOTIFIED_FILE, [])


def save_notified(ids):
    _save(NOTIFIED_FILE, ids)


def check_unread():
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    sender_query = " OR ".join(f"from:{s}" for s in get_senders())
    query = f"is:unread ({sender_query})"

    resp = requests.get(GMAIL_URL, headers=headers, params={"q": query, "maxResults": 10})
    resp.raise_for_status()
    messages = resp.json().get("messages", [])

    if not messages:
        return {"message": "No new mail", "ids": []}

    resp = requests.get(f"{GMAIL_URL}/{messages[0]['id']}", headers=headers, params={
        "format": "metadata", "metadataHeaders": ["From", "Subject"]
    })
    resp.raise_for_status()
    latest = resp.json()

    headers = {h["name"]: h["value"] for h in latest["payload"]["headers"]}
    sender = headers.get("From", "Unknown")
    subject = headers.get("Subject", "(no subject)")

    if "<" in sender:
        sender = sender.split("<")[0].strip().strip('"')

    count = len(messages)
    prefix = f"{count} new" if count > 1 else "New mail"

    return {"message": f"{prefix} - {sender}: {subject}", "responses": get_responses(),
            "id": messages[0]["id"], "ids": [m["id"] for m in messages]}


def reply_mail(msg_id, text):
    """Reply to message msg_id in its thread, then mark it as read."""
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    resp = requests.get(f"{GMAIL_URL}/{msg_id}", headers=headers, params={
        "format": "metadata", "metadataHeaders": ["From", "Subject", "Message-ID"]
    })
    resp.raise_for_status()
    original = resp.json()
    orig_headers = {h["name"].lower(): h["value"] for h in original["payload"]["headers"]}
    subject = orig_headers.get("subject", "")

    msg = EmailMessage()
    msg["To"] = orig_headers["from"]
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if "message-id" in orig_headers:
        msg["In-Reply-To"] = orig_headers["message-id"]
        msg["References"] = orig_headers["message-id"]
    msg.set_content(text)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = requests.post(f"{GMAIL_URL}/send", headers=headers, json={"raw": raw, "threadId": original["threadId"]})
    resp.raise_for_status()

    resp = requests.post(f"{GMAIL_URL}/{msg_id}/modify", headers=headers, json={"removeLabelIds": ["UNREAD"]})
    resp.raise_for_status()
