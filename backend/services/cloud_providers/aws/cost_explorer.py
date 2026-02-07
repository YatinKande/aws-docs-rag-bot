from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

class AWSCostExplorer:
    def __init__(self, client):
        self.ce = client.session.client('ce')

    async def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        end = datetime.now().date()
        start = end - timedelta(days=days)
        
        try:
            # Run blocking boto3 call in threadpool
            response = await asyncio.to_thread(
                self.ce.get_cost_and_usage,
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            return {
                "total": sum(float(r['Total']['UnblendedCost']['Amount']) for r in response['ResultsByTime']),
                "results": response['ResultsByTime'],
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
