import boto3
import datetime
import os

def download_latest_file(bucket_name, prefix, filename_prefix, local_path):
    """
    Downloads the latest CSV file from the given S3 bucket and prefix.
    The filename is expected to follow the format: prefix_YYYY-MM-DD.csv
    """
    s3 = boto3.client("s3")
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"{filename_prefix}_{today}.csv"
    key = f"{prefix}/{filename}"
    
    try:
        print(f"⬇️ Downloading s3://{bucket_name}/{key} to {local_path}")
        s3.download_file(bucket_name, key, local_path)
        print(f"✅ File downloaded: {local_path}")
    except Exception as e:
        print(f"❌ Failed to download file from S3: {e}")
        raise
