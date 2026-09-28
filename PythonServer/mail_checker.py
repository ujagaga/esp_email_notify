import json
import os.path

import requests

from config import SENDERS
from gmail_auth import get_access_token

GMAIL_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
SENDERS_FILE = os.path.join(os.path.dirname(__file__), "senders.json")
RESPONSES_FILE = os.path.join(os.path.dirname(__file__), "responses.json")


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


def check_unread():
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    sender_query = " OR ".join(f"from:{s}" for s in get_senders())
    query = f"is:unread ({sender_query})"

    resp = requests.get(GMAIL_URL, headers=headers, params={"q": query, "maxResults": 10})
    resp.raise_for_status()
    messages = resp.json().get("messages", [])

    if not messages:
        return {"beep": False, "message": "No new mail"}

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

    return {"beep": True, "message": f"{prefix} - {sender}: {subject}", "responses": get_responses()}
