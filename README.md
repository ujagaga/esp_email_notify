# ESP Email Notify

A small desk gadget that tells you when specific people email you, and lets you
send one of a few canned replies with the press of a button.

An ESP8266 with a Nokia 5110 LCD, a piezo speaker and two buttons shows the
latest unread mail from a list of watched senders and beeps when a new one
arrives. One button cycles through the prepared responses, the other sends the
selected one as a reply.

## How it works

```
  Gmail API  <--HTTPS/OAuth-->  Python server  <--HTTP on LAN-->  ESP8266
                                (this computer)                   (LCD, beep, buttons)
```

- **The server does all the mail work.** It holds the Google OAuth token,
  queries Gmail for unread mail from the configured senders, sends replies and
  marks replied mail as read. The ESP never talks to Google and holds no Google
  credentials. It is only a display, speaker and pair of buttons.
- **Polling, not push.** The ESP asks the server `/check` every few seconds,
  and each request makes the server query Gmail. The server only tells the ESP
  to beep once for each new message.
- **Zero-config discovery.** Server and ESP are on the same local network. The
  ESP broadcasts `email_check?` over UDP, and the server answers with its HTTP
  port. The ESP reads the server's IP from the reply, so neither side needs a
  static IP.
- **Replies in the thread.** Pressing OK sends the selected response as a
  normal reply to the shown message, then marks it read in Gmail.
- **Simple device setup.** After every start the ESP runs its own WiFi access
  point for 5 minutes, with a web page for choosing the home network. After
  that it switches to client-only mode.
- **Personal-use Google app.** The OAuth app is published but unverified, and
  asks for the single `gmail.modify` scope. Sign-in happens once, in a browser
  on the server machine. After that the server runs unattended on the saved
  refresh token.

## Repository layout

| Folder | What it is |
|---|---|
| [PythonServer/](PythonServer/) | Flask server: Gmail access, web page to sign in and edit senders and responses, device API, UDP discovery. Setup and API are described in its [README](PythonServer/README.md). |
| [ESP8266_client/](ESP8266_client/) | Arduino firmware for the ESP8266 D1 mini: wiring, build, flashing and WiFi setup are described in its [README](ESP8266_client/README.md). |

## Getting started

1. Set up and start the server ([PythonServer/README.md](PythonServer/README.md)),
   then sign in at `http://localhost:<port>` on the same machine.
2. Build and flash the firmware, then connect it to your WiFi
   ([ESP8266_client/README.md](ESP8266_client/README.md)).
3. The ESP finds the server by itself and starts showing mail.
