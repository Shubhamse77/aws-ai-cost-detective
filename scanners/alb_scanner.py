def scan_alb(session, region):
    """
    Scans a single region for unused/idle Application & Network Load Balancers (0 target instances).
    """
    elbv2_client = session.client('elbv2', region_name=region)
    findings = {
        "unused_albs": []
    }

    try:
        lbs = elbv2_client.describe_load_balancers().get('LoadBalancers', [])
        for lb in lbs:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']

            # Check target groups associated with this load balancer
            tgs = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn).get('TargetGroups', [])
            has_active_targets = False

            for tg in tgs:
                tg_arn = tg['TargetGroupArn']
                health = elbv2_client.describe_target_health(TargetGroupArn=tg_arn).get('TargetHealthDescriptions', [])
                if health:
                    has_active_targets = True
                    break

            # If no target groups or target groups have 0 registered targets, flag as unused
            if not has_active_targets:
                findings["unused_albs"].append({
                    "region": region,
                    "load_balancer_name": lb_name,
                    "arn": lb_arn,
                    "type": lb.get('Type', 'application')
                })

    except Exception as e:
        print(f"[!] [ALB] Error scanning region {region}: {e}")

    return findings
