import requests
import httpx
import asyncio
import json
import os
import pandas as pd
from datetime import datetime
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES, GOOGLE_APPLICATION_CREDENTIALS
import bq_upload
from threading import Thread
from prefect import flow, task
from dotenv import load_dotenv
#import traceback
load_dotenv()
load_dotenv(dotenv_path='.env')
print("CLIENT_ID:", os.getenv("TWITCH_CLIENT_ID"))
print("TWITCH_CLIENT_SECRET:", os.getenv("TWITCH_CLIENT_SECRET"))
print("TWITCH_REDIRECT_URI:", os.getenv("TWITCH_REDIRECT_URI"))
load_dotenv(dotenv_path=".env")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

TOKEN_FILE = "tokens.json"

def get_valid_token():
    try:
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
    #except FileNotFoundError:
    #    raise RuntimeError("No token file found. Please run the Flask login flow first.")
    except Exception as e:
        import traceback
        print("Error while refreshing token:")
        traceback.print_exc()  # full stack trace
        raise RuntimeError(f"Failed to refresh token: {str(e)}") from e

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
    
   
    print("Error while refreshing token:")
    #traceback.print_exc()  # full stack trace
    #raise RuntimeError(f"Failed to refresh token: {str(e)}") from e

    #raise RuntimeError("Failed to refresh token. Re-authentication required.")


async def fetch_streams_backup(access_token):
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


@task
def background_stream_fetcher(access_token):
    """Run the async function inside a thread-safe wrapper"""
    asyncio.run(get_streams_async(access_token))



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
                # Log or handle error instead of returning from async context
                print("Error fetching streams:", response.text)
                return

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

        # Upload to BigQuery
        try:
            bq_upload.upload_data(df)
        except Exception as e:
            print("BQ upload error:", e)

        # OPTIONAL: For debugging/logging only — DO NOT USE on Render
        print(f"Fetched {len(df)} streams at {datetime.now().isoformat()}")

@flow
def main():
    access_token = get_valid_token()
    background_stream_fetcher(access_token)
    #print(task_message)


@flow
def my_flow():
    print("Hello, Prefect!")


if __name__ == "__main__":
    main.serve(name="twitch-trial-deployment", cron="*/30 * * * *")