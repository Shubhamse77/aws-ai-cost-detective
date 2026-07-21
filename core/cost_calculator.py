# Standard AWS Global Average Unit Rates (Estimated monthly waste baseline)
ESTIMATED_RATES = {
    "eip_per_hour": 0.005,           # ~$3.60 / month per unattached EIP
    "ebs_gp3_per_gb_month": 0.08,    # ~$0.08 / GB-month for EBS gp3
    "snapshot_per_gb_month": 0.05,   # ~$0.05 / GB-month for Standard Snapshots
    "alb_base_per_month": 22.50,     # ~$22.50 / month base charge per idle ALB
}

# Approx baseline EC2 hourly cost estimates by instance family (if on-demand rate unavailable)
EC2_ESTIMATED_HOURLY = {
    "t2.micro": 0.0116, "t3.micro": 0.0104,
    "t3.small": 0.0208, "t3.medium": 0.0416,
    "t3.large": 0.0832, "t3.xlarge": 0.1664, "t3.2xlarge": 0.3328,
    "m5.large": 0.096,  "m5.xlarge": 0.192,  "r5.large": 0.126
}

def calculate_regional_waste(findings):
    """
    Enriches the multi-region JSON output with exact monthly estimated dollar waste per resource.
    """
    total_monthly_waste = 0.0
    enriched_findings = []

    for reg_data in findings:
        region = reg_data["region"]
        reg_waste = 0.0

        # 1. Calculate Unattached EBS Volume Waste
        unattached_vols = []
        for vol in reg_data.get("unattached_volumes", []):
            size_gb = vol.get("size_gb", 0)
            monthly_cost = size_gb * ESTIMATED_RATES["ebs_gp3_per_gb_month"]
            vol["estimated_monthly_waste_usd"] = round(monthly_cost, 2)
            reg_waste += monthly_cost
            unattached_vols.append(vol)

        # 2. Calculate Stale Snapshot Waste
        stale_snaps = []
        for snap in reg_data.get("stale_snapshots", []):
            size_gb = snap.get("volume_size_gb", 0)
            monthly_cost = size_gb * ESTIMATED_RATES["snapshot_per_gb_month"]
            snap["estimated_monthly_waste_usd"] = round(monthly_cost, 2)
            reg_waste += monthly_cost
            stale_snaps.append(snap)

        # 3. Calculate Unattached EIP Waste
        unattached_eips = []
        for eip in reg_data.get("unattached_eips", []):
            monthly_cost = ESTIMATED_RATES["eip_per_hour"] * 24 * 30  # ~$3.60/mo
            eip["estimated_monthly_waste_usd"] = round(monthly_cost, 2)
            reg_waste += monthly_cost
            unattached_eips.append(eip)

        # 4. Calculate Stopped EC2 EBS Storage Waste
        stopped_ec2s = []
        for ec2 in reg_data.get("stopped_ec2s", []):
            # Stopped EC2s still incur base storage cost (estimated ~30GB GP3 root vol average if unmeasured)
            estimated_ebs_cost = 30 * ESTIMATED_RATES["ebs_gp3_per_gb_month"]
            ec2["estimated_monthly_waste_usd"] = round(estimated_ebs_cost, 2)
            reg_waste += estimated_ebs_cost
            stopped_ec2s.append(ec2)

        # 5. Calculate Low CPU EC2 Instance Waste
        low_cpu_ec2s = []
        for ec2 in reg_data.get("low_cpu_ec2s", []):
            itype = ec2.get("instance_type", "t3.medium")
            hourly_rate = EC2_ESTIMATED_HOURLY.get(itype, 0.05)
            monthly_cost = hourly_rate * 24 * 30
            ec2["estimated_monthly_waste_usd"] = round(monthly_cost, 2)
            reg_waste += monthly_cost
            low_cpu_ec2s.append(ec2)

        # 6. Calculate Unused Load Balancer Waste
        unused_albs = []
        for alb in reg_data.get("unused_albs", []):
            monthly_cost = ESTIMATED_RATES["alb_base_per_month"]
            alb["estimated_monthly_waste_usd"] = round(monthly_cost, 2)
            reg_waste += monthly_cost
            unused_albs.append(alb)

        total_monthly_waste += reg_waste

        enriched_findings.append({
            "region": region,
            "regional_waste_usd": round(reg_waste, 2),
            "unattached_volumes": unattached_vols,
            "stale_snapshots": stale_snaps,
            "unattached_eips": unattached_eips,
            "stopped_ec2s": stopped_ec2s,
            "low_cpu_ec2s": low_cpu_ec2s,
            "unused_albs": unused_albs
        })

    return {
        "total_estimated_monthly_waste_usd": round(total_monthly_waste, 2),
        "regional_breakdown": enriched_findings
    }
