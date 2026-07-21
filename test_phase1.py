from config.aws_config import get_boto3_session, get_all_enabled_regions

def test_connection():
    print("--- Phase 1: Multi-Region Connection Test ---")
    session = get_boto3_session()
    
    # Verify STS identity (Caller Account)
    sts_client = session.client('sts')
    identity = sts_client.get_caller_identity()
    
    print(f"[✔] AWS Account ID: {identity['Account']}")
    print(f"[✔] IAM Identity:   {identity['Arn']}")
    
    # Fetch all enabled regions
    regions = get_all_enabled_regions(session)
    print(f"\n[✔] Multi-Region List ({len(regions)} regions):")
    for r in regions:
        print(f"  - {r}")

if __name__ == "__main__":
    test_connection()
