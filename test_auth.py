import os
from dotenv import load_dotenv
import praw

# Step 1: Load .env variables
load_dotenv()

client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
redirect_uri = os.getenv("REDDIT_REDIRECT_URI")
user_agent = os.getenv("REDDIT_USER_AGENT")

# Step 2: Validate all values are loaded
print("Loaded credentials:")
print("Client ID:", client_id)
print("Client Secret:", client_secret[:3] + "...")
print("Redirect URI:", redirect_uri)
print("User Agent:", user_agent)

if not all([client_id, client_secret, redirect_uri, user_agent]):
    raise Exception("Missing one or more required environment variables.")

# Step 3: Initialize Reddit instance
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    user_agent=user_agent
)

# Step 4: Generate auth URL
auth_url = reddit.auth.url(
    scopes=["identity", "read"],
    state="goatlandstate",
    duration="permanent"
)

print("\n✅ Visit this URL to authorize the app:")
print(auth_url)
