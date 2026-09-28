#!/usr/bin/env python3
import secrets

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from config import ADMIN_EMAIL, DEVICE_KEY, PORT
from gmail_auth import oauth, save_token
from mail_checker import check_unread, get_responses, get_senders, save_responses, save_senders

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
        status = {"beep": False, "message": "Could not check mail", "error": str(e)}
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
        return jsonify(check_unread())
    except Exception as e:
        return jsonify({"beep": False, "message": "Server error", "error": str(e)}), 503


@app.route("/authorize")
def authorize():
    return oauth.authorize_redirect(url_for("oauth2callback", _external=True))


@app.route("/oauth2callback")
def oauth2callback():
    token = oauth.authorize_access_token()
    email = oauth.get("userinfo").json().get("email")
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
