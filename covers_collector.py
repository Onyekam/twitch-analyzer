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
from dotenv import load_dotenv
import base64
#import traceback
load_dotenv()
load_dotenv(dotenv_path='.env')
print("CLIENT_ID:", os.getenv("TWITCH_CLIENT_ID"))
print("TWITCH_CLIENT_SECRET:", os.getenv("TWITCH_CLIENT_SECRET"))
print("TWITCH_REDIRECT_URI:", os.getenv("TWITCH_REDIRECT_URI"))
load_dotenv(dotenv_path=".env")
# Defer to ADC from Actions auth; only set if local, real file exists and not already set
if (
    not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    and isinstance(GOOGLE_APPLICATION_CREDENTIALS, str)
    and GOOGLE_APPLICATION_CREDENTIALS.endswith(".json")
    and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS)
):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
TOKEN_FILE = "tokens.json"
CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
REPO = os.environ.get("REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")
GH_PAT = os.environ.get("GH_PAT")


def get_valid_token():
    tokens = None

    # 1. Prefer GitHub secret (Actions env var)
    tokens_json = os.environ.get("TWITCH_TOKENS")
    if tokens_json:
        try:
            tokens = json.loads(tokens_json)
        except json.JSONDecodeError:
            raise RuntimeError("TWITCH_TOKENS secret is not valid JSON")

    # 2. Otherwise fallback to local file
    elif os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)

    else:
        raise RuntimeError("No tokens found. Set TWITCH_TOKENS or create tokens.json")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # Test if access token still works
    headers = {"Authorization": f"Bearer {access_token}", "Client-Id": CLIENT_ID}
    test_response = requests.get("https://api.twitch.tv/helix/users", headers=headers)

    if test_response.status_code == 200:
        return access_token

    # Refresh token
    print("Refreshing access token...")
    refresh_url = "https://id.twitch.tv/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(refresh_url, data=data)

    if response.status_code != 200:
        raise RuntimeError(f"Error refreshing token: {response.text}")

    new_tokens = response.json()

    # Save locally if dev
    if not os.environ.get("GITHUB_ACTIONS"):
        with open(TOKEN_FILE, "w") as f:
            json.dump(new_tokens, f, indent=2)
    else:
        update_github_secret("TWITCH_TOKENS", json.dumps(new_tokens))

    return new_tokens.get("access_token")


def update_github_secret(secret_name, secret_value):
    """Update a GitHub Actions secret using PAT instead of GITHUB_TOKEN"""
    print(f"Updating GitHub secret: {secret_name}")

    url = f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"Bearer {GH_PAT}",  # <-- PAT here
        "Accept": "application/vnd.github+json",
    }

    # Get repo public key - repo name should be updated 
    key_url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    key_resp = requests.get(key_url, headers=headers)
    key_resp.raise_for_status()
    key_data = key_resp.json()

    from nacl import encoding, public

    def encrypt(public_key: str, secret_value: str) -> str:
        public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    encrypted_value = encrypt(key_data["key"], secret_value)

    put_data = {
        "encrypted_value": encrypted_value,
        "key_id": key_data["key_id"],
    }
    put_resp = requests.put(url, headers=headers, json=put_data)
    put_resp.raise_for_status()
    print("Secret updated successfully ✅")




def background_covers_fetcher(access_token):
    """Run the async function inside a thread-safe wrapper"""
    asyncio.run(get_covers_async(access_token))



def flatten_covers_batch(data):
    """
    Flatten IGDB covers response into a clean DataFrame.
    """
    flat_data = []
    for cover in data:
        flat_cover = {}

        # --- ID ---
        try:
            flat_cover["id"] = int(cover.get("id"))
        except Exception:
            flat_cover["id"] = None

        # --- Game ID ---
        try:
            flat_cover["game"] = int(cover.get("game"))
        except Exception:
            flat_cover["game"] = None

        # --- URL ---
        url = cover.get("url")
        if url:
            # Convert thumbnail to higher-res if you want (replace t_thumb → t_cover_big)
            flat_cover["url"] = url.replace("t_thumb", "t_cover_big")
        else:
            flat_cover["url"] = None

        flat_data.append(flat_cover)

    return pd.DataFrame(flat_data)


async def get_covers_async(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID,
    }

    url = "https://api.igdb.com/v4/covers"
    batch_size = 500
    offset = 0
    total_fetched = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            query = f"fields id, game, url; limit {batch_size}; offset {offset};"
            response = await client.post(url, headers=headers, content=query)

            if response.status_code != 200:
                print("Error fetching covers:", response.text)
                break

            data = response.json()
            if not data:
                print("No more covers to fetch. Done ✅")
                break

            df = flatten_covers_batch(data)

            try:
                bq_upload.upload_covers_data(df)  # <-- you'll need a new function in bq_upload.py
            except Exception as e:
                print(f"BigQuery upload failed for offset {offset}: {e}")

            total_fetched += len(df)
            print(
                f"Fetched covers: offset={offset}, size={len(df)}, total={total_fetched}, time={datetime.now().isoformat()}"
            )

            offset += batch_size
            await asyncio.sleep(0.25)  # rate limit safety

def monitor_collection():
    try:
        requests.get("https://hc-ping.com/681f561e-7baa-404b-bb6c-43506773d617", timeout=10)
    except requests.RequestException as e:
        print("Ping failed: %s" % e)


def check_pat():
    url = f"https://api.github.com/repos/{REPO}"
    headers = {"Authorization": f"Bearer {GH_PAT}"}
    resp = requests.get(url, headers=headers)
    print("PAT check status:", resp.status_code, resp.json())



def main():
    access_token = get_valid_token()
    #check_pat()
    background_covers_fetcher(access_token)
    
    # adds monitoring
    monitor_collection()
    #print(task_message)


if __name__ == "__main__":
    main()