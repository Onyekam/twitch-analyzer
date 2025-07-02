from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("TWITCH_REDIRECT_URI")
SCOPES = "analytics:read:games analytics:read:extensions user:read:email"
PROJECT_ID=os.environ.get("PROJECT_ID")
DATASET_ID=os.environ.get("DATASET_ID")
TABLE_ID=os.environ.get("TABLE_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")