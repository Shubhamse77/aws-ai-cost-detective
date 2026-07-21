import json
from concurrent.futures import ThreadPoolExecutor
from config.aws_config import get_boto3_session, get_all_enabled_regions
from scanners.ebs_scanner import scan_ebs
from scanners.eip_scanner import scan_eips
from scanners.ec2_scanner import scan_ec2
from scanners.alb_scanner import scan_load_balancers

def scan_region_worker(session, region):
    """Worker function to scan a single region for all resource waste categories."""
    print(f"[*] Scanning region: {region}...")
    
    ebs_res = scan_ebs(session, region)
    eip_res = scan_eips(session, region)
    ec2_res = scan_ec2(session, region)
    alb_res = scan_load_balancers(session, region)

    return {
        "region": region,
        "unattached_volumes": ebs_res["unattached_volumes"],
        "stale_snapshots": ebs_res["stale_snapshots"],
        "unattached_eips": eip_res,
        "stopped_ec2s": ec2_res["stopped_instances"],
        "low_cpu_ec2s": ec2_res["low_cpu_instances"],
        "unused_albs": alb_res
    }

def main():
    print("=== Phase 2: Starting Multi-Region Cloud Cost Audit ===")
    session = get_boto3_session()
    regions = get_all_enabled_regions(session)

    aggregated_results = {
        "summary": {"total_regions_scanned": len(regions)},
        "findings": []
    }

    # Parallelize region scanning using thread pool for speed
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_region_worker, session, region) for region in regions]
        for future in futures:
            aggregated_results["findings"].append(future.result())

    # Save output report locally
    with open("multi_region_waste_report.json", "w") as f:
        json.dump(aggregated_results, f, indent=2)

    print("\n[✔] Multi-region scan complete!")
    print(f"[✔] Comprehensive audit saved to 'multi_region_waste_report.json'")

if __name__ == "__main__":
    main()
