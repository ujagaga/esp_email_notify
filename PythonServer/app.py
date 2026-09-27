import secrets

from flask import Flask, jsonify, request

from config import DEVICE_KEY, PORT
from mail_checker import check_unread

app = Flask(__name__)


@app.route("/check")
def check():
    key = request.headers.get("X-Api-Key", "")
    if not secrets.compare_digest(key, DEVICE_KEY):
        return jsonify({"error": "unauthorized"}), 401

    try:
        return jsonify(check_unread())
    except Exception as e:
        return jsonify({"beep": False, "message": "Server error", "error": str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
