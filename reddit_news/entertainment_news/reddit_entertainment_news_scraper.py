import os
from dotenv import load_dotenv
import praw
import csv
import boto3
from datetime import datetime

# Load .env file
load_dotenv()

# Load credentials from environment
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Validate required environment variables
required = {
    "REDDIT_CLIENT_ID": REDDIT_CLIENT_ID,
    "REDDIT_CLIENT_SECRET": REDDIT_CLIENT_SECRET,
    "REDDIT_USER_AGENT": REDDIT_USER_AGENT,
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
    "AWS_REGION": AWS_REGION,
    "S3_BUCKET_NAME": S3_BUCKET_NAME,
}
for key, value in required.items():
    if not value:
        raise ValueError(f"Missing environment variable: {key}")

# Initialize Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Subreddits to pull from
subreddits = ["entertainment", "movies", "television"]

def fetch_top_entertainment_posts(limit=5):
    results = []
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.hot(limit=limit):
            if not post.stickied:
                results.append({
                    "title": post.title,
                    "url": post.url,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "score": post.score,
                    "subreddit": sub
                })
    return results

def save_posts_to_csv(posts, filename):
    fieldnames = ["title", "url", "permalink", "score", "subreddit"]
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(posts)

def upload_to_s3(filename, bucket_name, s3_path):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    s3.upload_file(Filename=filename, Bucket=bucket_name, Key=s3_path)
    print(f"Uploaded {filename} to s3://{bucket_name}/{s3_path}")

if __name__ == "__main__":
    posts = fetch_top_entertainment_posts()

    for post in posts:
        print(f"[{post['subreddit']}] {post['title']} ({post['score']} points)")
        print(f"Link: {post['permalink']}\n")

    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"reddit_entertainment_news_{today}.csv"
    save_posts_to_csv(posts, filename)

    s3_key = f"reddit_entertainment_news/{filename}"
    upload_to_s3(filename, S3_BUCKET_NAME, s3_key)
