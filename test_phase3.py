import json
from config.aws_config import get_boto3_session, get_all_enabled_regions
from run_multi_region_scan import scan_region_worker
from core.cost_explorer import get_monthly_spend_by_service
from core.cost_calculator import calculate_regional_waste
from concurrent.futures import ThreadPoolExecutor

def main():
    print("=== Phase 3: Cost Explorer & Savings Calculation ===")
    session = get_boto3_session()
    regions = get_all_enabled_regions(session)

    # 1. Fetch AWS Cost Explorer Historical Spend
    print("\n[*] Querying AWS Cost Explorer API for 30-day account spend...")
    service_costs = get_monthly_spend_by_service(session)
    
    # 2. Execute Multi-Region Waste Audit
    print(f"[*] Auditing resource waste across {len(regions)} enabled region(s)...")
    raw_findings = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_region_worker, session, region) for region in regions]
        for future in futures:
            raw_findings.append(future.result())

    # 3. Enrich Findings with Estimated Dollar ($) Waste Calculations
    cost_analysis = calculate_regional_waste(raw_findings)

    # 4. Construct Final Master Data Payload
    master_payload = {
        "account_id": session.client('sts').get_caller_identity()['Account'],
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_estimated_monthly_waste_usd": cost_analysis["total_estimated_monthly_waste_usd"],
        "top_account_spend_30_days": service_costs[:5],  # Top 5 costly services
        "regional_findings": cost_analysis["regional_breakdown"]
    }

    # Save to file
    with open("ai_input_payload.json", "w") as f:
        json.dump(master_payload, f, indent=2)

    print("\n" + "="*50)
    print(f"[✔] Total Estimated Monthly Waste Identified: ${master_payload['total_estimated_monthly_waste_usd']:.2f} USD")
    print(f"[✔] Master AI Input Payload generated & saved to 'ai_input_payload.json'")
    print("="*50)

if __name__ == "__main__":
    from datetime import datetime, timezone
    main()
