from flask import Flask, redirect, request, jsonify
import requests
import json
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES

app = Flask(__name__)
TOKEN_FILE = "tokens.json"

@app.route("/")
def home():
    return "Twitch Auth App is running. Visit /login to begin authentication."

@app.route("/login")
def login():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES
    }
    return redirect(f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Missing code in callback."

    token_url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(token_url, data=payload)
    tokens = response.json()

    # Store tokens securely (file, DB, etc.)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    return "Authorization successful. Tokens saved!"

@app.route("/refresh")
def refresh():
    try:
        with open(TOKEN_FILE) as f:
            refresh_token = json.load(f).get("refresh_token")
    except Exception:
        return "No tokens saved."

    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    tokens = response.json()

    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    return jsonify(tokens)

@app.route("/user")
def get_user():
    try:
        with open(TOKEN_FILE) as f:
            access_token = json.load(f).get("access_token")
    except Exception:
        return "No access token found."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID
    }
    response = requests.get("https://api.twitch.tv/helix/users", headers=headers)
    return jsonify(response.json())