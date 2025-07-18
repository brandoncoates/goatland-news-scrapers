import os
import boto3
import openai
import datetime
from shared.openai_utils import get_openai_client
from shared.s3_utils import download_latest_file

S3_BUCKET = "fantasy-sports-csvs"
REDDIT_BUCKET = "news-headlines-csvs"

file_sources = {
    "boxscores": ("baseball/boxscores", "mlb_boxscores"),
    "espn_articles": ("baseball/news", "mlb_espn_articles"),
    "rosters": ("baseball/rosters", "mlb_rosters"),
    "weather": ("baseball/weather", "mlb_weather"),
    "probable_starters": ("baseball/probablestarters", "mlb_probable_starters"),
    "betting_odds": ("baseball/betting", "mlb_betting_odds"),
    "reddit_fantasy": ("reddit_fantasy_baseball", "reddit_fantasy_baseball"),
}

def download_latest_file_from_s3(s3_client, prefix, filename_prefix, local_path):
    print(f"Attempting to download: s3://{S3_BUCKET}/{prefix}/{filename_prefix}_YYYY-MM-DD.csv")
    return download_latest_file(S3_BUCKET, prefix, filename_prefix, local_path)

def download_latest_reddit_file(s3_client, prefix, filename_prefix, local_path):
    print(f"Attempting to download: s3://{REDDIT_BUCKET}/{prefix}/{filename_prefix}_YYYY-MM-DD.csv")
    return download_latest_file(REDDIT_BUCKET, prefix, filename_prefix, local_path)

def load_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(data):
    today = datetime.date.today().strftime("%B %d, %Y")
    prompt = f"""You are a professional fantasy baseball analyst writing a DFS advice article for {today}.

Use the following CSV content sources to write your article:

1. **Box Scores (Yesterday)**:
{data['boxscores'][:1500]}

2. **ESPN Fantasy Article (Hitter Projections)**:
{data['espn_articles'][:1500]}

3. **Reddit Fantasy Baseball Highlights**:
{data['reddit_fantasy'][:1500]}

4. **Weather Reports**:
{data['weather'][:1000]}

5. **Probable Starters (Pitching Matchups)**:
{data['probable_starters'][:1000]}

6. **Betting Odds**:
{data['betting_odds'][:1000]}

7. **Roster Info (Injuries/Callups)**:
{data['rosters'][:1000]}

Your article should include:
- 2–3 Pitchers to Target (based on matchups, weather, and value)
- 1–2 Pitchers to Fade
- 2–3 Hitters to Target at Each Position (C, 1B, 2B, 3B, SS, OF)
- Any Team Stacks that make sense based on matchups, weather, or Vegas odds
- Brief recap of how yesterday’s picks performed (based on boxscores)
- Callouts to news or injuries (from Reddit and roster data)

Be concise and sharp, as if writing for a daily fantasy sports blog. Use bullet points or sections to keep it readable.
"""
    return prompt

def main():
    s3 = boto3.client("s3")
    local_data = {}

    for key, (prefix, filename_prefix) in file_sources.items():
        local_path = f"/tmp/{filename_prefix}.csv"
        try:
            if key == "reddit_fantasy":
                download_latest_reddit_file(s3, prefix, filename_prefix, local_path)
            else:
                download_latest_file_from_s3(s3, prefix, filename_prefix, local_path)
            local_data[key] = load_csv(local_path)
        except Exception as e:
            print(f"⚠️ Failed to download {key}: {e}")
            local_data[key] = ""

    print("✅ Generating DFS article with OpenAI...")
    client = get_openai_client()
    prompt = build_prompt(local_data)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional fantasy baseball analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
    except Exception as e:
        print("❌ OpenAI API error:", e)
        raise

    today = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = os.path.join("shared", "generated_dfs_articles")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"fantasy_dfs_article_{today}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ DFS article saved to: {output_path}")

if __name__ == "__main__":
    main()
