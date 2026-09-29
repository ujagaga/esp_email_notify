import json
import os.path
import time

from oauth import ManualGoogleOAuth

SCOPE = ("https://www.googleapis.com/auth/gmail.readonly "
         "https://www.googleapis.com/auth/gmail.send")
BASE_DIR = os.path.dirname(__file__)
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

oauth = ManualGoogleOAuth(CREDENTIALS_FILE, scope=SCOPE)


def save_token(token):
    token["expires_at"] = time.time() + token["expires_in"] - 60
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)


def get_access_token():
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError("Not authorized, open /authorize in a browser")

    with open(TOKEN_FILE) as f:
        token = json.load(f)

    if time.time() >= token["expires_at"]:
        refreshed = oauth.refresh_access_token(token["refresh_token"])
        token.update(refreshed)  # refresh response has no refresh_token, keep the old one
        save_token(token)

    return token["access_token"]
