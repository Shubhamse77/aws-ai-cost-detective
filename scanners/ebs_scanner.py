from datetime import datetime, timezone

def scan_ebs(session, region, days=90):
    """
    Scans a single region for:
    1. Unattached EBS volumes
    2. Stale EBS snapshots older than `days`
    3. GP2 volumes eligible for GP3 migration (Attached/In-Use ONLY)
    """
    ec2_client = session.client('ec2', region_name=region)
    findings = {
        "unattached_volumes": [],
        "stale_snapshots": [],
        "gp2_volumes": []
    }

    try:
        # Scan Volumes
        vols_res = ec2_client.describe_volumes()
        for vol in vols_res.get('Volumes', []):
            vol_id = vol['VolumeId']
            state = vol['State']
            size = vol['Size']
            vol_type = vol['VolumeType']

            tags = {t['Key']: t['Value'] for t in vol.get('Tags', [])}
            name = tags.get('Name', 'N/A')

            # Check 1: Unattached Volumes
            if state == 'available':
                findings["unattached_volumes"].append({
                    "region": region,
                    "volume_id": vol_id,
                    "size_gb": size,
                    "name": name
                })
            
            # Check 2: GP2 to GP3 Migration Candidates (ONLY IF ATTACHED / IN-USE)
            if vol_type == 'gp2' and state == 'in-use':
                findings["gp2_volumes"].append({
                    "region": region,
                    "volume_id": vol_id,
                    "size_gb": size,
                    "name": name,
                    "current_type": "gp2"
                })

        # Scan Snapshots
        snaps_res = ec2_client.describe_snapshots(OwnerIds=['self'])
        for snap in snaps_res.get('Snapshots', []):
            snap_id = snap['SnapshotId']
            start_time = snap['StartTime']
            vol_size = snap.get('VolumeSize', 0)

            age_days = (datetime.now(timezone.utc) - start_time).days
            if age_days > days:
                findings["stale_snapshots"].append({
                    "region": region,
                    "snapshot_id": snap_id,
                    "volume_size_gb": vol_size,
                    "age_days": age_days
                })

    except Exception as e:
        print(f"[!] [EBS] Error scanning region {region}: {e}")

    return findings
