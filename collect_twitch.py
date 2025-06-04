from flask import Flask, redirect, request, jsonify
import requests
import json
import os
import asyncio
import httpx
import pandas as pd
from datetime import datetime
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES

app = Flask(__name__)
TOKEN_FILE = "tokens.json"

@app.route("/")
def home():
    print(f'redirect uri: {os.getenv("TWITCH_REDIRECT_URI")}')
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

def get_valid_token():
    try:
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
    except FileNotFoundError:
        return None, redirect("/login")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # Check if token is still valid by trying a simple API call
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID
    }
    test_response = requests.get("https://api.twitch.tv/helix/users", headers=headers)

    # If token is valid
    if test_response.status_code == 200:
        return access_token, None

    # Try refreshing the token
    refresh_url = "https://id.twitch.tv/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(refresh_url, data=data)

    if response.status_code == 200:
        new_tokens = response.json()
        with open(TOKEN_FILE, "w") as f:
            json.dump(new_tokens, f, indent=2)
        return new_tokens.get("access_token"), None

    # If refresh fails, force re-login
    return None, redirect("/login")



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

@app.route("/streams")
def get_streams():
    access_token, redirect_response = get_valid_token()
    if redirect_response:
        return redirect_response

    return asyncio.run(get_streams_async(access_token))

async def get_streams_async(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID
    }

    all_streams = []
    url = "https://api.twitch.tv/helix/streams"
    params = {"first": 100}

    async with httpx.AsyncClient() as client:
        page_count = 0
        while True:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                return jsonify({"error": response.json()}), response.status_code

            data = response.json()
            all_streams.extend(data.get("data", []))

            pagination = data.get("pagination", {})
            cursor = pagination.get("cursor")

            page_count += 1
            if not cursor:
                break

            if page_count % 5 == 0:
                await asyncio.sleep(1)

            params["after"] = cursor

        df = pd.DataFrame(all_streams)
        now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        df.to_json(f"streams-{now}.ndjson", orient="records", lines=True)

    return jsonify({"data": all_streams})


if __name__ == "__main__":
    app.run()