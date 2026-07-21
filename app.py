import streamlit as st
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from config.aws_config import get_boto3_session, get_all_enabled_regions
from run_multi_region_scan import scan_region_worker
from core.cost_explorer import get_monthly_spend_by_service
from core.cost_calculator import calculate_regional_waste
from core.ai_detective import run_ai_analysis

# Page Configuration
st.set_page_config(
    page_title="AI Cloud Cost Detective",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 AI Cloud Cost Detective (AWS Multi-Region)")
st.caption("Automated FinOps Audit Engine across all enabled AWS Regions")

# Sidebar Controls
st.sidebar.header("Configuration & Actions")
if st.sidebar.button("🚀 Run Multi-Region Cost Audit", type="primary"):
    with st.spinner("Authenticating and scanning active AWS regions..."):
        session = get_boto3_session()
        regions = get_all_enabled_regions(session)

        # 1. Fetch AWS Cost Explorer Historical Spend
        service_costs = get_monthly_spend_by_service(session)

        # 2. Parallel Region Scanning
        raw_findings = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(scan_region_worker, session, region) for region in regions]
            for future in futures:
                raw_findings.append(future.result())

        # 3. Enrich with Cost Estimations
        cost_analysis = calculate_regional_waste(raw_findings)

        # 4. Create Master Payload
        master_payload = {
            "account_id": session.client('sts').get_caller_identity()['Account'],
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_estimated_monthly_waste_usd": cost_analysis["total_estimated_monthly_waste_usd"],
            "top_account_spend_30_days": service_costs[:5],
            "regional_findings": cost_analysis["regional_breakdown"]
        }

        # 5. Run AI Reasoning Analysis
        ai_response = run_ai_analysis(master_payload)

        # Save to Streamlit Session State
        st.session_state["master_payload"] = master_payload
        st.session_state["ai_response"] = ai_response
        st.sidebar.success("Audit Completed Successfully!")

# Display Results if Available
if "master_payload" in st.session_state:
    payload = st.session_state["master_payload"]
    ai_res = st.session_state["ai_response"]
    summary = ai_res.get("audit_summary", {})

    # Top Metric Highlights
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Est. Monthly Waste", f"${payload['total_estimated_monthly_waste_usd']:.2f}")
    col2.metric("Actionable Items", summary.get("total_actionable_items", 0))
    col3.metric("Low Risk Items", summary.get("risk_breakdown", {}).get("LOW_RISK", 0))
    col4.metric("AWS Account ID", payload["account_id"])

    st.markdown("---")

    # Tabs for Data Organization
    tab1, tab2, tab3 = st.tabs(["💡 AI Remediation Plan", "🌍 Regional Waste Breakdown", "📊 Account Spend (30 Days)"])

    # TAB 1: AI Recommendations Table
    with tab1:
        st.subheader("AI-Generated Cost Optimization Recommendations")
        recs = ai_res.get("recommendations", [])

        if recs:
            for rec in recs:
                risk_color = "🟢" if rec["risk_level"] == "LOW_RISK" else "🟡" if rec["risk_level"] == "MEDIUM_RISK" else "🔴"
                
                with st.expander(f"{risk_color} [{rec['region']}] {rec['resource_type']} - {rec['resource_id']} (${rec['estimated_monthly_savings_usd']:.2f}/mo)"):
                    st.write(f"**Reason:** {rec['reason']}")
                    st.write(f"**Risk Rating:** {rec['risk_level']}")
                    st.code(rec['remediation_cli'], language="bash")
        else:
            st.success("🎉 No idle resources or cost waste detected in your active AWS regions!")

    # TAB 2: Regional Findings
    with tab2:
        st.subheader("Resource Waste per Region")
        for reg_data in payload.get("regional_findings", []):
            if reg_data["regional_waste_usd"] > 0:
                st.markdown(f"### 📍 Region: `{reg_data['region']}` — Est. Waste: **${reg_data['regional_waste_usd']:.2f} USD/mo**")
                
                if reg_data["unattached_volumes"]:
                    st.write("**Unattached EBS Volumes:**", len(reg_data["unattached_volumes"]))
                if reg_data["unattached_eips"]:
                    st.write("**Unattached Elastic IPs:**", len(reg_data["unattached_eips"]))
                if reg_data["stopped_ec2s"]:
                    st.write("**Stopped EC2 Instances:**", len(reg_data["stopped_ec2s"]))
                if reg_data["unused_albs"]:
                    st.write("**Unused Load Balancers:**", len(reg_data["unused_albs"]))
                st.markdown("---")

    # TAB 3: Top Spend Services
    with tab3:
        st.subheader("Top Historical Account Costs (Last 30 Days)")
        spend_data = payload.get("top_account_spend_30_days", [])
        if spend_data:
            st.table(spend_data)
        else:
            st.info("AWS Cost Explorer data is empty or permissions (`ce:GetCostAndUsage`) need to be granted.")

else:
    st.info("Click **🚀 Run Multi-Region Cost Audit** in the sidebar to scan your AWS environment.")

# Footer Section
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Built with ❤️ by <b>Shubham Thakur</b> | AWS AI Cloud Cost Detective</div>", 
    unsafe_allow_html=True
)
