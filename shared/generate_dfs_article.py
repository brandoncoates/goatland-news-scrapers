import os
import boto3
import pandas as pd
from datetime import datetime, timedelta
import openai

# --- CONFIG ---
S3_BUCKET = 'news-headlines-csvs'
S3_PREFIXES = {
    'boxscores': 'mlb_boxscores',
    'rosters': 'mlb_rosters',
    'weather': 'mlb_weather',
    'starters': 'mlb_probable_starters',
    'odds': 'mlb_betting_odds',
    'espn': 'mlb_espn_articles',
    'reddit': 'reddit_fantasy_baseball'
}

# Set up OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up AWS S3
s3 = boto3.client('s3')

# --- UTILITY FUNCTION ---
def download_latest_file(prefix):
    today = datetime.utcnow().date()
    key = f"{prefix}/{prefix}_{today}.csv"
    local_path = f"/tmp/{prefix}.csv"
    s3.download_file(S3_BUCKET, key, local_path)
    return pd.read_csv(local_path)

# --- LOAD ALL FILES ---
def load_all_csvs():
    return {
        name: download_latest_file(prefix)
        for name, prefix in S3_PREFIXES.items()
    }

# --- PROMPT CREATION ---
def build_prompt(data_dict):
    prompt = "You are a fantasy baseball expert writing today's DFS article.\n"
    prompt += "Use the following CSV data to recommend players to target or avoid. Consider performance, matchups, weather, odds, and value.\n\n"
    for name, df in data_dict.items():
        prompt += f"\n## {name.upper()} DATA ##\n"
        prompt += df.head(20).to_csv(index=False)
    prompt += "\n\nWrite a compelling DFS article for today based on this data."
    return prompt

# --- MAIN ---
def main():
    print("Loading data from S3...")
    data = load_all_csvs()

    print("Building prompt...")
    prompt = build_prompt(data)

    print("Sending to OpenAI...")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1800
    )

    article = response['choices'][0]['message']['content']

    print("Saving article...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_path = f"shared/generated_dfs_articles/dfs_article_{today_str}.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(article)

    print(f"✅ DFS article saved to {output_path}")

if __name__ == "__main__":
    main()
