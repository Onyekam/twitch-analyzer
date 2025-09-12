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

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

TOKEN_FILE = "tokens.json"


CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
REPO = os.environ.get("REPOSITORY")
GH_PAT = os.environ.get("GH_PAT")

def get_valid_token_backup():
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



async def fetch_games_backup(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID
    }

    all_games = []
    url = "https://api.igdb.com/v4/games"
    params = {"first": 100}

    async with httpx.AsyncClient() as client:
        page_count = 0
        while True:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print("Error response:", response.text)
                raise Exception(f"Error fetching games: {response.status_code}")

            data = response.json()
            all_games.extend(data.get("data", []))

            pagination = data.get("pagination", {})
            cursor = pagination.get("cursor")
            page_count += 1

            if not cursor:
                break

            if page_count % 5 == 0:
                await asyncio.sleep(1)

            params["after"] = cursor

    return all_games


def background_games_fetcher(access_token):
    """Run the async function inside a thread-safe wrapper"""
    asyncio.run(get_games_async(access_token))



async def get_games_async(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": CLIENT_ID,
    }

    url = "https://api.igdb.com/v4/games"
    batch_size = 500
    offset = 0
    total_fetched = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            # IGDB requires POST with body query
            query = f"fields id, name, genres.name, platforms.name, summary; limit {batch_size}; offset {offset};"

            response = await client.post(url, headers=headers, content=query)
            if response.status_code != 200:
                print("Error fetching games:", response.text)
                break

            data = response.json()
            if not data:
                print("No more games to fetch. Done ✅")
                break

            # Flatten and upload
            df = flatten_games_batch(data)
            try:
                bq_upload.upload_game_data(df)
            except Exception as e:
                print(f"BigQuery upload failed for offset {offset}: {e}")

            total_fetched += len(df)
            print(
                f"Fetched batch: offset={offset}, size={len(df)}, total={total_fetched}, time={datetime.now().isoformat()}"
            )

            # Prepare next batch
            offset += batch_size
            await asyncio.sleep(0.25)  # small delay for rate limiting

def monitor_collection():
    try:
        requests.get("https://hc-ping.com/1573d1fb-6e6b-4356-a036-c506310fa0d8", timeout=10)
    except requests.RequestException as e:
        print("Ping failed: %s" % e)


def check_pat():
    url = f"https://api.github.com/repos/{REPO}"
    headers = {"Authorization": f"Bearer {GH_PAT}"}
    resp = requests.get(url, headers=headers)
    print("PAT check status:", resp.status_code, resp.json())


def flatten_games_batch(data):
    """
    Convert raw IGDB batch into a clean DataFrame for BigQuery.
    Ensures all fields are primitive (int/string) — no nested objects.
    """
    flat_data = []

    for game in data:
        flat_game = {}

        # --- ID (force int or None) ---
        raw_id = game.get("id")
        if isinstance(raw_id, list) and raw_id:
            flat_game["id"] = int(raw_id[0])
        elif isinstance(raw_id, dict) and "value" in raw_id:
            flat_game["id"] = int(raw_id["value"])
        else:
            try:
                flat_game["id"] = int(raw_id)
            except Exception:
                flat_game["id"] = None

        # --- Name ---
        flat_game["name"] = game.get("name")

        # --- Genres ---
        genres = game.get("genres")
        if genres and isinstance(genres, list):
            flat_game["genres"] = ", ".join(
                [str(g.get("name", "")) for g in genres if isinstance(g, dict)]
            )
        else:
            flat_game["genres"] = None

        # --- Platforms ---
        platforms = game.get("platforms")
        if platforms and isinstance(platforms, list):
            flat_game["platforms"] = ", ".join(
                [str(p.get("name", "")) for p in platforms if isinstance(p, dict)]
            )
        else:
            flat_game["platforms"] = None

        # --- Summary ---
        flat_game["summary"] = game.get("summary")

        flat_data.append(flat_game)

    return pd.DataFrame(flat_data)


def main():
    access_token = get_valid_token()
    #check_pat()
    background_games_fetcher(access_token)
    
    # adds monitoring
    #monitor_collection()
    #print(task_message)


if __name__ == "__main__":
    main()