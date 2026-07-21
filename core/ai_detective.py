import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are an expert AWS FinOps Architect and AI Cloud Cost Detective.
Your role is to analyze multi-region AWS resource scan data and provide actionable cost-optimization recommendations.

For each issue found in the data, provide:
1. Resource Identifier & Region
2. Risk Rating: LOW_RISK (safe to delete immediately), MEDIUM_RISK (needs verification), HIGH_RISK (requires approval)
3. Reason & Potential Monthly Savings ($)
4. Safe Remediation Code (AWS CLI command)

Return ONLY valid JSON matching this schema:
{
  "audit_summary": {
    "total_monthly_savings_usd": 0.0,
    "total_actionable_items": 0,
    "risk_breakdown": {"LOW_RISK": 0, "MEDIUM_RISK": 0, "HIGH_RISK": 0}
  },
  "recommendations": [
    {
      "region": "us-east-1",
      "resource_type": "Unattached EBS Volume / Unused EIP / Stopped EC2 / Idle ALB",
      "resource_id": "vol-1234567890",
      "risk_level": "LOW_RISK",
      "estimated_monthly_savings_usd": 15.00,
      "reason": "Unattached GP3 EBS volume accumulated costs without active compute attachment.",
      "remediation_cli": "aws ec2 delete-volume --volume-id vol-1234567890 --region us-east-1"
    }
  ]
}
"""

def analyze_with_bedrock(payload_json):
    """Invokes Amazon Bedrock (Claude 3.5 Sonnet / Claude 3) with multi-region payload."""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

        prompt = f"Analyze this AWS multi-region cost audit data and output JSON matching system schema:\n\n{json.dumps(payload_json, indent=2)}"

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        })

        response = bedrock_runtime.invoke_model(modelId=model_id, body=body)
        response_body = json.loads(response.get('body').read())
        raw_text = response_body['content'][0]['text']
        return json.loads(raw_text)
    except Exception as e:
        print(f"[!] Bedrock Analysis Error: {e}")
        return generate_fallback_analysis(payload_json)

def generate_fallback_analysis(payload_json):
    """Rule-based fallback engine if external LLM API is unavailable."""
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

        # 2. Unattached EIPs
        for eip in reg_data.get("unattached_eips", []):
            recommendations.append({
                "region": region,
                "resource_type": "Unattached Elastic IP",
                "resource_id": eip["public_ip"],
                "risk_level": "LOW_RISK",
                "estimated_monthly_savings_usd": eip.get("estimated_monthly_waste_usd", 3.60),
                "reason": "Elastic IP allocated but not associated with an EC2 instance.",
                "remediation_cli": f"aws ec2 release-address --allocation-id {eip['allocation_id']} --region {region}"
            })

        # 3. Stopped EC2s
        for ec2 in reg_data.get("stopped_ec2s", []):
            recommendations.append({
                "region": region,
                "resource_type": "Stopped EC2 Instance",
                "resource_id": ec2["instance_id"],
                "risk_level": "MEDIUM_RISK",
                "estimated_monthly_savings_usd": ec2.get("estimated_monthly_waste_usd", 2.40),
                "reason": f"Instance ({ec2['name']}) is stopped but continues to incur EBS storage fees.",
                "remediation_cli": f"aws ec2 terminate-instances --instance-ids {ec2['instance_id']} --region {region}"
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
        return analyze_with_bedrock(payload_json)
    else:
        return generate_fallback_analysis(payload_json)
