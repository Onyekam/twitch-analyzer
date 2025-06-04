import requests
import httpx
import asyncio
import json
import os
import pandas as pd
from datetime import datetime
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES

TOKEN_FILE = "tokens.json"

def get_valid_token():
    try:
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
    except FileNotFoundError:
        raise RuntimeError("No token file found. Please run the Flask login flow first.")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID
    }
    test_response = requests.get("https://api.twitch.tv/helix/users", headers=headers)

    if test_response.status_code == 200:
        return access_token

    # Try refreshing the token
    print("Refreshing access token...")
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
        return new_tokens.get("access_token")

    raise RuntimeError("Failed to refresh token. Re-authentication required.")


async def fetch_streams(access_token):
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
                print("Error response:", response.text)
                raise Exception(f"Error fetching streams: {response.status_code}")

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

    return all_streams


def main():
    try:
        access_token = get_valid_token()
        streams_data = asyncio.run(fetch_streams(access_token))

        if streams_data:
            df = pd.DataFrame(streams_data)
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            filename = f"streams-{timestamp}.ndjson"
            df.to_json(filename, orient="records", lines=True)
            print(f"Saved {len(df)} streams to {filename}")
        else:
            print("No stream data collected.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()