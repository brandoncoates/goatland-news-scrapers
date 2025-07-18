import os
import boto3
import datetime
import pandas as pd

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Set up AWS + OpenAI
s3 = boto3.client("s3")
bucket_name = "news-headlines-csvs"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

today = datetime.date.today().strftime("%Y-%m-%d")

# Define expected files with correct keys
s3_files = {
    "mlb_boxscores": f"mlb_boxscores_{today}.csv",
    "mlb_espn_articles": f"mlb_espn_articles_{today}.csv",
    "mlb_rosters": f"mlb_rosters_{today}.csv",
    "mlb_weather": f"mlb_weather_{today}.csv",
    "mlb_probable_starters": f"mlb_probable_starters_{today}.csv",
    "mlb_betting_odds": f"mlb_betting_odds_{today}.csv",
    "reddit_fantasy_baseball": f"reddit_fantasy_baseball_{today}.csv"
}

# Create tmp folder
os.makedirs("shared/tmp", exist_ok=True)

# Download files from S3
local_paths = {}
for key, filename in s3_files.items():
    local_path = f"shared/tmp/{filename}"
    s3_key = f"{key}/{filename}"
    try:
        print(f"📥 Attempting to download: s3://{bucket_name}/{s3_key}")
        s3.download_file(bucket_name, s3_key, local_path)
        print(f"✅ Downloaded: {s3_key}")
        local_paths[key] = local_path
    except Exception as e:
        print(f"❌ Failed to download {s3_key}: {e}")

# Load data (only those that downloaded successfully)
loaded_data = {}
for key, path in local_paths.items():
    try:
        loaded_data[key] = pd.read_csv(path)
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")

# Build system prompt
system_prompt = """
You are a fantasy baseball expert helping users build their daily DFS lineups.

You will be given:
- Box scores from the previous day
- Today's starting pitchers and weather
- Team rosters with injury statuses
- ESPN hitter picks
- Reddit fantasy baseball discussion
- Vegas odds (totals, spreads, moneylines)

Write a single DFS article with:
1. Pitchers to target (explain why)
2. Pitchers to fade (explain why)
3. Top hitter picks by position (1B, 2B, 3B, SS, OF, C, UTIL)
4. Suggested stacks by team
5. Weather impact (skip domes)
6. Value plays (compare to expected salary)

Tone: helpful, sharp, insightful. Don’t list full lineups. Prioritize context and reasoning behind each pick.
"""

# Build user message
user_message = "Here are today's files:\n\n"
for key, df in loaded_data.items():
    preview = df.head(10).to_csv(index=False)
    user_message += f"\n\n=== {key.upper()} ===\n{preview}"

# Run OpenAI completion
print("🧠 Generating DFS article with OpenAI...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_message.strip()}
    ],
    temperature=0.7
)

# Extract content
article_text = response.choices[0].message.content.strip()

# Save article
os.makedirs("shared/generated_dfs_articles", exist_ok=True)
output_path = f"shared/generated_dfs_articles/dfs_article_{today}.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(article_text)

print(f"✅ DFS article saved to {output_path}")
