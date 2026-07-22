def scan_eip(session, region):
    """
    Scans a single region for unattached Elastic IPs (EIPs).
    """
    ec2_client = session.client('ec2', region_name=region)
    findings = {
        "unattached_eips": []
    }

    try:
        addresses = ec2_client.describe_addresses().get('Addresses', [])
        for addr in addresses:
            # An EIP without an InstanceId or NetworkInterfaceId is unattached
            if 'InstanceId' not in addr and 'NetworkInterfaceId' not in addr:
                findings["unattached_eips"].append({
                    "region": region,
                    "allocation_id": addr.get('AllocationId', 'N/A'),
                    "public_ip": addr.get('PublicIp', 'N/A')
                })

    except Exception as e:
        print(f"[!] [EIP] Error scanning region {region}: {e}")

    return findings
