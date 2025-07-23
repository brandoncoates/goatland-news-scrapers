import praw
import json
import os
from datetime import datetime
import boto3

# Set up Reddit API connection using environment variables
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent=os.environ["REDDIT_USER_AGENT"]
)

# Get today's date for filename
today = datetime.now().strftime("%Y-%m-%d")
csv_filename = f"reddit_fantasybaseball_articles_{today}.csv"
json_filename = csv_filename.replace(".csv", ".json")
folder_name = "reddit_fantasy_baseball"
s3_key = f"{folder_name}/{json_filename}"

# Pull top 10 posts from r/fantasybaseball
subreddit = reddit.subreddit("fantasybaseball")
posts = subreddit.hot(limit=15)

articles = []
for post in posts:
    if not post.stickied:
        articles.append({
            "title": post.title,
            "score": post.score,
            "url": post.url,
            "permalink": f"https://www.reddit.com{post.permalink}"
        })
        if len(articles) >= 10:
            break

# Save to JSON
json_path = f"/tmp/{json_filename}"
with open(json_path, mode="w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"💾 JSON file written locally: {json_path}")

# Upload to S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

s3.upload_file(json_path, os.environ["S3_BUCKET_NAME"], s3_key)
print(f"☁️ Uploaded to S3: {s3_key}")

# Cleanup temp file
os.remove(json_path)
print(f"🧹 Cleaned up local file {json_path}")
