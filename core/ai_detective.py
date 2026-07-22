import os

def generate_fallback_analysis(payload_json):
    recommendations = []
    total_savings = payload_json.get("total_estimated_monthly_waste_usd", 0.0)

    for reg_data in payload_json.get("regional_findings", []):
        region = reg_data["region"]

        # 1. Unattached EBS
        for vol in reg_data.get("unattached_volumes", []):
            recommendations.append({
                "region": region,
                "resource_type": "Unattached EBS Volume",
                "resource_id": vol["volume_id"],
                "risk_level": "LOW_RISK",
                "estimated_monthly_savings_usd": vol.get("estimated_monthly_waste_usd", 0.0),
                "reason": f"Unattached volume ({vol['size_gb']} GB) in state 'available'.",
                "remediation_cli": f"aws ec2 delete-volume --volume-id {vol['volume_id']} --region {region}"
            })

        # 2. Stale Snapshots
        for snap in reg_data.get("stale_snapshots", []):
            recommendations.append({
                "region": region,
                "resource_type": "Stale EBS Snapshot",
                "resource_id": snap["snapshot_id"],
                "risk_level": "LOW_RISK",
                "estimated_monthly_savings_usd": snap.get("estimated_monthly_waste_usd", 0.0),
                "reason": f"Snapshot older than 90 days ({snap['age_days']} days old).",
                "remediation_cli": f"aws ec2 delete-snapshot --snapshot-id {snap['snapshot_id']} --region {region}"
            })

        # 3. GP2 to GP3 Migration (Attached Volumes)
        for vol in reg_data.get("gp2_volumes", []):
            vol_id = vol["volume_id"]
            recommendations.append({
                "region": region,
                "resource_type": "GP2 Volume (Migrate to GP3)",
                "resource_id": vol_id,
                "risk_level": "LOW_RISK",
                "estimated_monthly_savings_usd": vol.get("estimated_monthly_waste_usd", 0.0),
                "reason": f"Attached volume '{vol['name']}' ({vol['size_gb']} GB) uses legacy gp2 storage. Migrating to gp3 saves 20% on monthly storage costs with zero downtime.",
                "remediation_cli": f"aws ec2 modify-volume --volume-id {vol_id} --volume-type gp3 --region {region}"
            })

        # 4. Unattached EIPs
        for eip in reg_data.get("unattached_eips", []):
            recommendations.append({
                "region": region,
                "resource_type": "Unattached Elastic IP",
                "resource_id": eip["public_ip"],
                "risk_level": "LOW_RISK",
                "estimated_monthly_savings_usd": eip.get("estimated_monthly_waste_usd", 3.60),
                "reason": "Elastic IP allocated but not attached to an EC2 instance.",
                "remediation_cli": f"aws ec2 release-address --allocation-id {eip['allocation_id']} --region {region}"
            })

        # 5. Stopped EC2s
        for ec2 in reg_data.get("stopped_ec2s", []):
            recommendations.append({
                "region": region,
                "resource_type": "Stopped EC2 Instance",
                "resource_id": ec2["instance_id"],
                "risk_level": "MEDIUM_RISK",
                "estimated_monthly_savings_usd": ec2.get("estimated_monthly_waste_usd", 2.40),
                "reason": f"Instance ({ec2['name']}) is stopped but continues incurring EBS charges.",
                "remediation_cli": f"aws ec2 terminate-instances --instance-ids {ec2['instance_id']} --region {region}"
            })

        # 6. Unused Load Balancers
        for alb in reg_data.get("unused_albs", []):
            recommendations.append({
                "region": region,
                "resource_type": "Unused Load Balancer",
                "resource_id": alb["load_balancer_name"],
                "risk_level": "MEDIUM_RISK",
                "estimated_monthly_savings_usd": alb.get("estimated_monthly_waste_usd", 22.50),
                "reason": f"Load Balancer '{alb['load_balancer_name']}' has 0 active targets.",
                "remediation_cli": f"aws elbv2 delete-load-balancer --load-balancer-arn {alb['arn']} --region {region}"
            })

    return {
        "audit_summary": {
            "total_monthly_savings_usd": total_savings,
            "total_actionable_items": len(recommendations),
            "risk_breakdown": {
                "LOW_RISK": len([r for r in recommendations if r["risk_level"] == "LOW_RISK"]),
                "MEDIUM_RISK": len([r for r in recommendations if r["risk_level"] == "MEDIUM_RISK"]),
                "HIGH_RISK": len([r for r in recommendations if r["risk_level"] == "HIGH_RISK"])
            }
        },
        "recommendations": recommendations
    }

def run_ai_analysis(payload_json):
    provider = os.getenv("LLM_PROVIDER", "fallback").lower()
    if provider == "bedrock":
        from core.ai_detective import analyze_with_bedrock
        return analyze_with_bedrock(payload_json)
    else:
        return generate_fallback_analysis(payload_json)
