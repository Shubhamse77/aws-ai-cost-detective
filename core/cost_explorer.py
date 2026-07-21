from datetime import datetime, timedelta, timezone

def get_monthly_spend_by_service(session):
    """
    Queries AWS Cost Explorer for unblended spend grouped by AWS Service for the past 30 days.
    """
    ce_client = session.client('ce', region_name='us-east-1')
    
    end_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')

    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        service_costs = []
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                if amount > 0.01:  # Only capture non-trivial spend
                    service_costs.append({
                        "service": service_name,
                        "monthly_cost_usd": round(amount, 2)
                    })

        # Sort by highest spend first
        return sorted(service_costs, key=lambda x: x['monthly_cost_usd'], reverse=True)

    except Exception as e:
        print(f"[!] [CostExplorer] Could not fetch spend (Ensure 'ce:GetCostAndUsage' permissions are granted): {e}")
        return []
