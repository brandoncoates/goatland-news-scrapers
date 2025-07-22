import os
from dotenv import load_dotenv
import praw
import csv
import boto3
from datetime import datetime

# ───── Load .env ─────
load_dotenv()

# ───── Credentials from env ─────
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT")
AWS_ACCESS_KEY_ID    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY= os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION           = os.getenv("AWS_REGION")
S3_BUCKET_NAME       = os.getenv("S3_BUCKET_NAME")

# ───── Validate ─────
required = {
    "REDDIT_CLIENT_ID": REDDIT_CLIENT_ID,
    "REDDIT_CLIENT_SECRET": REDDIT_CLIENT_SECRET,
    "REDDIT_USER_AGENT": REDDIT_USER_AGENT,
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
    "AWS_REGION": AWS_REGION,
    "S3_BUCKET_NAME": S3_BUCKET_NAME,
}
for k, v in required.items():
    if not v:
        raise ValueError(f"Missing environment variable: {k}")

# ───── Init Reddit client ─────
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# ───── Config ─────
SUBREDDIT   = "gamernews"
LIMIT       = 5
today       = datetime.today().strftime("%Y-%m-%d")
filename    = f"reddit_gamer_news_{today}.csv"
s3_key      = f"reddit_gamer_news/{filename}"

# ───── Fetch top posts ─────
def fetch_top_gamer_posts(limit=LIMIT):
    posts = []
    for post in reddit.subreddit(SUBREDDIT).hot(limit=limit):
        if post.stickied:
            continue
        posts.append({
            "title":     post.title,
            "url":       post.url,
            "permalink": f"https://reddit.com{post.permalink}",
            "score":     post.score,
            "subreddit": SUBREDDIT,
        })
    return posts

# ───── CSV writer ─────
def save_posts_to_csv(posts, path):
    fieldnames = ["title", "url", "permalink", "score", "subreddit"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(posts)

# ───── Upload to S3 ─────
def upload_to_s3(local_path, bucket, key):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    s3.upload_file(Filename=local_path, Bucket=bucket, Key=key)
    print(f"Uploaded {local_path} → s3://{bucket}/{key}")

# ───── Main ─────
if __name__ == "__main__":
    posts = fetch_top_gamer_posts()
    for p in posts:
        print(f"[{p['subreddit']}] {p['title']} ({p['score']} pts)\n{p['permalink']}\n")
    save_posts_to_csv(posts, filename)
    upload_to_s3(filename, S3_BUCKET_NAME, s3_key)
