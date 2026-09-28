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
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python app.py`
5. Open `<server-url>` in a browser and sign in with `ADMIN_EMAIL`. This saves
   `token.json` (with a refresh token), after which the server runs unattended.
   While signed in, the page shows the current mail status.

## API

`GET /check`, header `X-Api-Key: <device_key>`

Response:
```json
{"beep": true, "message": "New mail - Alice: Meeting notes", "responses": ["On my way", "Call you later"]}
```

`beep` is `true` only when the reply contains unread mail that was not in the
previous `/check` reply, so the ESP beeps once per new message. `responses`
(edited on the `/config` page) is only present when there is unread mail.

`POST /send`, header `X-Api-Key: <device_key>`, form fields `to` (recipient
address) and `text` (used as both subject and body). Sends from the
`ADMIN_EMAIL` Gmail account.

```bash
curl -H "X-Api-Key: <device_key>" --data-urlencode "to=alice@example.com" \
     --data-urlencode "text=On my way" <server-url>/send
```

Response: `{"ok": true}`, or `{"error": "..."}` with status 400/401/503.
