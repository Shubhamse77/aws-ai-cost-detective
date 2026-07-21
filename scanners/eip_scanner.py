def scan_eips(session, region):
    """
    Scans a single region for Elastic IPs that are NOT associated with any EC2 or ENI.
    """
    ec2_client = session.client('ec2', region_name=region)
    unattached_eips = []

    try:
        response = ec2_client.describe_addresses()
        for addr in response.get('Addresses', []):
            # EIP is unattached if AssociationId is missing
            if 'AssociationId' not in addr:
                unattached_eips.append({
                    "region": region,
                    "allocation_id": addr.get('AllocationId'),
                    "public_ip": addr.get('PublicIp')
                })
    except Exception as e:
        print(f"[!] [EIP] Error scanning region {region}: {e}")

    return unattached_eips
