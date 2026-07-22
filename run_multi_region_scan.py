from scanners.ebs_scanner import scan_ebs
from scanners.eip_scanner import scan_eip
from scanners.ec2_scanner import scan_ec2
from scanners.alb_scanner import scan_alb

def scan_region_worker(session, region):
    ebs = scan_ebs(session, region)
    eip = scan_eip(session, region)
    ec2 = scan_ec2(session, region)
    alb = scan_alb(session, region)

    return {
        "region": region,
        "unattached_volumes": ebs.get("unattached_volumes", []),
        "stale_snapshots": ebs.get("stale_snapshots", []),
        "gp2_volumes": ebs.get("gp2_volumes", []),
        "unattached_eips": eip.get("unattached_eips", []),
        "stopped_ec2s": ec2.get("stopped_instances", []),
        "low_cpu_ec2s": ec2.get("low_cpu_instances", []),
        "unused_albs": alb.get("unused_albs", [])
    }
