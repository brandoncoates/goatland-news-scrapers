import os
import praw
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDIRECT_URI = os.getenv("REDDIT_REDIRECT_URI")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Set up Reddit instance
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret="",
    redirect_uri=REDIRECT_URI,
    user_agent=USER_AGENT
)

# OAuth scopes you want
scopes = ["identity", "read"]

# Step 1: Generate the auth URL
auth_url = reddit.auth.url(scopes=scopes, state="UNIQUE_STATE", duration="permanent")
print("🔗 Visit this URL and authorize access:\n", auth_url)
webbrowser.open(auth_url)

# Step 2: Create a simple HTTP server to catch the redirect
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"You may now close this window.")
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]
        if code:
            refresh_token = reddit.auth.authorize(code)
            print("\n✅ SUCCESS! Your refresh token:\n", refresh_token)
        else:
            print("\n❌ Failed to retrieve code.")

# Step 3: Listen on localhost for the OAuth callback
print("🌐 Waiting for Reddit callback on localhost:8080...")
httpd = HTTPServer(("localhost", 8080), Handler)
httpd.handle_request()
