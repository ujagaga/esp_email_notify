from config import SENDERS
from gmail_auth import get_gmail_service


def check_unread():
    service = get_gmail_service()
    sender_query = " OR ".join(f"from:{s}" for s in SENDERS)
    query = f"is:unread ({sender_query})"

    result = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
    messages = result.get("messages", [])

    if not messages:
        return {"beep": False, "message": "No new mail"}

    latest = service.users().messages().get(
        userId="me", id=messages[0]["id"], format="metadata",
        metadataHeaders=["From", "Subject"]
    ).execute()

    headers = {h["name"]: h["value"] for h in latest["payload"]["headers"]}
    sender = headers.get("From", "Unknown")
    subject = headers.get("Subject", "(no subject)")

    if "<" in sender:
        sender = sender.split("<")[0].strip().strip('"')

    count = len(messages)
    prefix = f"{count} new" if count > 1 else "New mail"

    return {"beep": True, "message": f"{prefix} - {sender}: {subject}"}
