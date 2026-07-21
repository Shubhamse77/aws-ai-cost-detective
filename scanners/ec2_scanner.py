from datetime import datetime, timedelta, timezone

def scan_ec2(session, region, cpu_threshold=5.0, days=14):
    """
    Scans a single region for:
    1. Stopped EC2 instances
    2. Low CPU instances (< cpu_threshold% over 'days' period)
    """
    ec2_client = session.client('ec2', region_name=region)
    cw_client = session.client('cloudwatch', region_name=region)
    
    findings = {
        "stopped_instances": [],
        "low_cpu_instances": []
    }

    try:
        response = ec2_client.describe_instances()
        for res in response.get('Reservations', []):
            for inst in res.get('Instances', []):
                inst_id = inst['InstanceId']
                inst_type = inst['InstanceType']
                state = inst['State']['Name']

                # Extract Name tag if present
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

                # Check 2: Running instances with low average CPU
                elif state == 'running':
                    end_time = datetime.now(timezone.utc)
                    start_time = end_time - timedelta(days=days)

                    cw_res = cw_client.get_metric_data(
                        MetricDataQueries=[{
                            'Id': 'm1',
                            'MetricStat': {
                                'Metric': {
                                    'Namespace': 'AWS/EC2',
                                    'MetricName': 'CPUUtilization',
                                    'Dimensions': [{'Name': 'InstanceId', 'Value': inst_id}]
                                },
                                'Period': 86400,  # 1 day intervals
                                'Stat': 'Average'
                            }
                        }],
                        StartTime=start_time,
                        EndTime=end_time
                    )

                    values = cw_res['MetricDataResults'][0].get('Values', [])
                    if values:
                        avg_cpu = sum(values) / len(values)
                        if avg_cpu < cpu_threshold:
                            findings["low_cpu_instances"].append({
                                "region": region,
                                "instance_id": inst_id,
                                "instance_type": inst_type,
                                "name": name,
                                "avg_cpu_percent": round(avg_cpu, 2)
                            })

    except Exception as e:
        print(f"[!] [EC2] Error scanning region {region}: {e}")

    return findings
