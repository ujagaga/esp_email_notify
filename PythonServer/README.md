# Email checker server

Flask service that checks Gmail for unread mail from configured senders and
reports it to the ESP8266, which is just a display/beep drone.

## Setup

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, enable the **Gmail API**, and create an OAuth client ID of type
   **Desktop app**. Download it as `credentials.json` into this folder.
2. Copy `config.json.example` to `config.json` and fill in:
   - `device_key`: a GUID for the ESP to authenticate with (generate one with
     `python -c "import uuid; print(uuid.uuid4())"`).
   - `senders`: list of email addresses to watch for.
3. Install dependencies: `pip install -r requirements.txt`
4. Run `python gmail_auth.py` once, locally, on a machine with a browser. This
   opens a Google sign-in/consent page and creates `token.json`. Copy both
   `credentials.json` and `token.json` to wherever the server is deployed.
5. Run the server: `python app.py`

## API

`GET /check`, header `X-Api-Key: <device_key>`

Response:
```json
{"beep": true, "message": "New mail - Alice: Meeting notes"}
```
