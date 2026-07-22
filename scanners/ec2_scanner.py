def scan_ec2(session, region):
    """
    Scans a single region for:
    1. Stopped EC2 instances
    """
    ec2_client = session.client('ec2', region_name=region)
    
    findings = {
        "stopped_instances": []
    }

    try:
        response = ec2_client.describe_instances()
        for res in response.get('Reservations', []):
            for inst in res.get('Instances', []):
                inst_id = inst['InstanceId']
                inst_type = inst['InstanceType']
                state = inst['State']['Name']

                tags = {t['Key']: t['Value'] for t in inst.get('Tags', [])}
                name = tags.get('Name', 'N/A')

                # Check 1: Stopped instances
                if state == 'stopped':
                    findings["stopped_instances"].append({
                        "region": region,
                        "instance_id": inst_id,
                        "instance_type": inst_type,
                        "name": name
                    })

    except Exception as e:
        print(f"[!] [EC2] Error scanning region {region}: {e}")

    return findings
