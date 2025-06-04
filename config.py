from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("TWITCH_REDIRECT_URI")  # e.g., https://your-app.onrender.com/callback
SCOPES = "analytics:read:games analytics:read:extensions user:read:email"