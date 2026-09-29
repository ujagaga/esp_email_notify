#!/usr/bin/env python3
import secrets
import socket
import threading

import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from config import ADMIN_EMAIL, DEVICE_KEY, DISCOVERY_PORT, PORT
from gmail_auth import oauth, save_token
from mail_checker import (check_unread, get_notified, get_responses, get_senders, save_notified,
                          save_responses, save_senders, send_mail)

app = Flask(__name__)
app.secret_key = DEVICE_KEY  # stable across processes, so the OAuth session survives under CGI
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)


@app.route("/")
def home():
    email = session.get("email")
    if email != ADMIN_EMAIL:
        return render_template("login.html")

    try:
        status = check_unread()
    except Exception as e:
        status = {"message": "Could not check mail", "error": str(e)}
    return render_template("home.html", email=email, status=status)


@app.route("/config", methods=["GET", "POST"])
def config_page():
    email = session.get("email")
    if email != ADMIN_EMAIL:
        return redirect("/")

    if request.method == "POST":
        senders = [s.strip() for s in request.form.get("senders", "").splitlines() if s.strip()]
        responses = [r.strip() for r in request.form.get("responses", "").splitlines() if r.strip()]
        if senders:
            save_senders(senders)
            save_responses(responses)
            flash("Configuration saved.")
        else:
            flash("Enter at least one sender.")
        return redirect("/config")

    return render_template("config.html", email=email, senders=get_senders(), responses=get_responses())


@app.route("/check")
def check():
    key = request.headers.get("X-Api-Key", "")
    if not secrets.compare_digest(key, DEVICE_KEY):
        return jsonify({"error": "unauthorized"}), 401

    try:
        status = check_unread()
    except Exception as e:
        return jsonify({"beep": False, "message": "Server error", "error": str(e)}), 503

    # Beep only for unread mail the ESP was not told about in a previous reply
    ids = status.pop("ids")
    status["beep"] = bool(set(ids) - set(get_notified()))
    save_notified(ids)
    return jsonify(status)


@app.route("/send", methods=["POST"])
def send():
    key = request.headers.get("X-Api-Key", "")
    if not secrets.compare_digest(key, DEVICE_KEY):
        return jsonify({"error": "unauthorized"}), 401

    to, text = request.form.get("to", "").strip(), request.form.get("text", "").strip()
    if not to or not text:
        return jsonify({"error": "'to' and 'text' are required"}), 400

    try:
        send_mail(to, text)
    except Exception as e:
        return jsonify({"error": str(e)}), 503
    return jsonify({"ok": True})


@app.route("/authorize")
def authorize():
    return oauth.authorize_redirect(url_for("oauth2callback", _external=True))


@app.route("/oauth2callback")
def oauth2callback():
    token = oauth.authorize_access_token()
    resp = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/profile",
                        headers={"Authorization": f"Bearer {token['access_token']}"})
    resp.raise_for_status()
    email = resp.json().get("emailAddress")
    if email != ADMIN_EMAIL:
        flash(f"{email} is not allowed to use this site.")
        return redirect("/")

    if "refresh_token" not in token:
        flash("Google returned no refresh token, please sign in again.")
        return redirect("/")

    save_token(token)
    session["email"] = email
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def discovery():
    """Answer "email_check?" on DISCOVERY_PORT with "email_check:<PORT>", so the ESP can find the server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))
    reply = f"email_check:{PORT}".encode()

    while True:
        data, addr = sock.recvfrom(64)
        if data == b"email_check?":
            try:
                sock.sendto(reply, addr)
            except OSError:  # e.g. network went down, keep listening
                pass


if __name__ == "__main__":
    threading.Thread(target=discovery, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
