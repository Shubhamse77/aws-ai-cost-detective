import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def get_boto3_session():
    """Initializes and returns a boto3 session using default credentials or AWS CLI profile."""
    try:
        session = boto3.Session(
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        return session
    except Exception as e:
        print(f"[!] Error creating boto3 session: {e}")
        raise

def get_all_enabled_regions(session=None):
    """
    Dynamically fetches all active/enabled AWS regions for the account.
    Prevents scanning disabled regions (e.g., Opt-In regions like ap-east-1 if not enabled).
    """
    if not session:
        session = get_boto3_session()

    ec2_client = session.client('ec2', region_name='us-east-1')
    
    try:
        response = ec2_client.describe_regions(
            AllRegions=False  # Only returns enabled regions for this account
        )
        regions = [region['RegionName'] for region in response['Regions']]
        print(f"[+] Successfully fetched {len(regions)} enabled AWS region(s).")
        return sorted(regions)
    except ClientError as e:
        print(f"[!] Failed to fetch AWS regions: {e}")
        return ["us-east-1"]  # Fallback to us-east-1 if call fails

if __name__ == "__main__":
    sess = get_boto3_session()
    all_regions = get_all_enabled_regions(sess)
    print("Enabled Regions:", all_regions)
