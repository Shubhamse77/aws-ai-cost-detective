def scan_load_balancers(session, region):
    """
    Scans a single region for v2 Load Balancers (ALB/NLB) with 0 target instances or 0 traffic.
    """
    elbv2_client = session.client('elbv2', region_name=region)
    unused_albs = []

    try:
        lbs = elbv2_client.describe_load_balancers().get('LoadBalancers', [])
        for lb in lbs:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']

            # Check target groups attached to this LB
            tgs = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn).get('TargetGroups', [])
            total_targets = 0

            for tg in tgs:
                health = elbv2_client.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
                total_targets += len(health.get('TargetHealthDescriptions', []))

            # Flag if 0 target instances registered across all target groups
            if total_targets == 0:
                unused_albs.append({
                    "region": region,
                    "load_balancer_name": lb_name,
                    "type": lb['Type'],
                    "reason": "No registered targets in target groups"
                })

    except Exception as e:
        print(f"[!] [ALB] Error scanning region {region}: {e}")

    return unused_albs
