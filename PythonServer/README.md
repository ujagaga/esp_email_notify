# Email checker server

Flask service that checks Gmail for unread mail from configured senders and
reports it to the ESP8266, which is just a display/beep drone.

## Setup

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, enable the **Gmail API**, and create an OAuth client ID of type
   **Web application**. Add `<server-url>/oauth2callback` as an authorized
   redirect URI (Google allows only `https://...` or `http://localhost:<port>`).
   Download it as `credentials.json` into this folder.
2. Copy `config.py.example` to `config.py` and fill in:
   - `DEVICE_KEY`: a GUID for the ESP to authenticate with (generate one with
     `python -c "import uuid; print(uuid.uuid4())"`).
   - `SENDERS`: list of email addresses to watch for.
   - `ADMIN_EMAIL`: the Gmail account to check; the only one allowed to sign in.
   - `DISCOVERY_PORT`: UDP port for finding the server. Broadcasting
     `email_check?` to it gets the reply `email_check:<PORT>` from the server's IP.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python app.py`
5. Open `<server-url>` in a browser and sign in with `ADMIN_EMAIL`. This saves
   `token.json` (with a refresh token), after which the server runs unattended.
   While signed in, the page shows the current mail status.

## API

`GET /check`, header `X-Api-Key: <device_key>`

Response:
```json
{"beep": true, "message": "New mail - Alice: Meeting notes", "id": "18c2f...", "responses": ["On my way", "Call you later"]}
```

`beep` is `true` only when the reply contains unread mail that was not in the
previous `/check` reply, so the ESP beeps once per new message. `id` (the
latest unread message) and `responses` (edited on the `/config` page) are only
present when there is unread mail.

`POST /send`, header `X-Api-Key: <device_key>`, form fields `id` (message id
from `/check`) and `text` (reply body). Replies to that message's sender in the
same thread from the `ADMIN_EMAIL` Gmail account, then marks the message read.

```bash
curl -H "X-Api-Key: <device_key>" --data-urlencode "id=18c2f..." \
     --data-urlencode "text=On my way" <server-url>/send
```

Response: `{"ok": true}`, or `{"error": "..."}` with status 400/401/503.
