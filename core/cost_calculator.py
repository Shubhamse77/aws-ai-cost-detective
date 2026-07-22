ESTIMATED_RATES = {
    "eip_per_hour": 0.005,             # ~$3.60 / month
    "ebs_gp2_per_gb_month": 0.10,      # $0.10 / GB-month
    "ebs_gp3_per_gb_month": 0.08,      # $0.08 / GB-month (Save $0.02/GB-month)
    "snapshot_per_gb_month": 0.05,     # $0.05 / GB-month
    "alb_base_per_month": 22.50,       # ~$22.50 / month
}

EC2_MONTHLY_RATES = {
    "t2.micro": 8.35,   "t3.micro": 7.48,
    "t3.small": 14.97,  "t3.medium": 29.95,
    "t3.large": 59.90,  "t3.xlarge": 119.80,  "t3.2xlarge": 239.60,
    "m5.large": 69.12,  "m5.xlarge": 138.24,  "m5.2xlarge": 276.48,
    "r5.large": 90.72,  "r5.xlarge": 181.44,  "r5.2xlarge": 362.88
}

def calculate_regional_waste(findings):
    total_monthly_waste = 0.0
    enriched_findings = []

    for reg_data in findings:
        region = reg_data["region"]
        reg_waste = 0.0

        # 1. Unattached EBS
        unattached_vols = []
        for vol in reg_data.get("unattached_volumes", []):
            cost = vol.get("size_gb", 0) * ESTIMATED_RATES["ebs_gp3_per_gb_month"]
            vol["estimated_monthly_waste_usd"] = round(cost, 2)
            reg_waste += cost
            unattached_vols.append(vol)

        # 2. Stale Snapshots
        stale_snaps = []
        for snap in reg_data.get("stale_snapshots", []):
            cost = snap.get("volume_size_gb", 0) * ESTIMATED_RATES["snapshot_per_gb_month"]
            snap["estimated_monthly_waste_usd"] = round(cost, 2)
            reg_waste += cost
            stale_snaps.append(snap)

        # 3. GP2 to GP3 Migration (NEW)
        gp2_vols = []
        for vol in reg_data.get("gp2_volumes", []):
            savings = vol.get("size_gb", 0) * (ESTIMATED_RATES["ebs_gp2_per_gb_month"] - ESTIMATED_RATES["ebs_gp3_per_gb_month"])
            vol["estimated_monthly_waste_usd"] = round(savings, 2)
            reg_waste += savings
            gp2_vols.append(vol)

        # 4. Unattached EIPs
        unattached_eips = []
        for eip in reg_data.get("unattached_eips", []):
            cost = ESTIMATED_RATES["eip_per_hour"] * 24 * 30
            eip["estimated_monthly_waste_usd"] = round(cost, 2)
            reg_waste += cost
            unattached_eips.append(eip)

        # 5. Stopped EC2s
        stopped_ec2s = []
        for ec2 in reg_data.get("stopped_ec2s", []):
            cost = 30 * ESTIMATED_RATES["ebs_gp3_per_gb_month"]
            ec2["estimated_monthly_waste_usd"] = round(cost, 2)
            reg_waste += cost
            stopped_ec2s.append(ec2)

        # 6. Low CPU EC2s
        low_cpu_ec2s = []
        for ec2 in reg_data.get("low_cpu_ec2s", []):
            itype = ec2.get("instance_type", "t3.medium")
            cost = EC2_MONTHLY_RATES.get(itype, 30.0)
            ec2["estimated_monthly_waste_usd"] = round(cost, 2)
            reg_waste += cost
            low_cpu_ec2s.append(ec2)

        # 7. Unused Load Balancers
        unused_albs = []
        for alb in reg_data.get("unused_albs", []):
            cost = ESTIMATED_RATES["alb_base_per_month"]
            alb["estimated_monthly_waste_usd"] = round(cost, 2)
            reg_waste += cost
            unused_albs.append(alb)

        total_monthly_waste += reg_waste

        enriched_findings.append({
            "region": region,
            "regional_waste_usd": round(reg_waste, 2),
            "unattached_volumes": unattached_vols,
            "stale_snapshots": stale_snaps,
            "gp2_volumes": gp2_vols,
            "unattached_eips": unattached_eips,
            "stopped_ec2s": stopped_ec2s,
            "low_cpu_ec2s": low_cpu_ec2s,
            "unused_albs": unused_albs
        })

    return {
        "total_estimated_monthly_waste_usd": round(total_monthly_waste, 2),
        "regional_breakdown": enriched_findings
    }
