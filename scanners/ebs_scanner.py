from datetime import datetime, timezone

def scan_ebs(session, region, max_snapshot_days=90):
    """
    Scans a single AWS region for:
    1. EBS volumes in 'available' state (unattached)
    2. Snapshots older than max_snapshot_days
    """
    ec2_client = session.client('ec2', region_name=region)
    findings = {
        "unattached_volumes": [],
        "stale_snapshots": []
    }

    try:
        # 1. Fetch unattached volumes
        vol_response = ec2_client.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        for vol in vol_response.get('Volumes', []):
            findings["unattached_volumes"].append({
                "region": region,
                "volume_id": vol['VolumeId'],
                "size_gb": vol['Size'],
                "volume_type": vol['VolumeType'],
                "create_time": vol['CreateTime'].isoformat()
            })

        # 2. Fetch account-owned snapshots older than max_snapshot_days
        snap_response = ec2_client.describe_snapshots(OwnerIds=['self'])
        now = datetime.now(timezone.utc)

        for snap in snap_response.get('Snapshots', []):
            age_days = (now - snap['StartTime']).days
            if age_days > max_snapshot_days:
                findings["stale_snapshots"].append({
                    "region": region,
                    "snapshot_id": snap['SnapshotId'],
                    "volume_size_gb": snap.get('VolumeSize', 0),
                    "age_days": age_days,
                    "description": snap.get('Description', '')
                })

    except Exception as e:
        print(f"[!] [EBS] Error scanning region {region}: {e}")

    return findings
