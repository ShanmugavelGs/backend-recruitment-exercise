import os
import httpx
from typing import Optional
from .models import MetricsPayload


class MetricsClient:
    def __init__(self):
        self.metrics_url = os.getenv("METRICS_LAMBDA_URL")
        self.timeout = float(os.getenv("METRICS_TIMEOUT", "30.0"))

    async def send_metrics(self, metrics: MetricsPayload) -> bool:
        if not self.metrics_url:
            print("Warning: METRICS_LAMBDA_URL not configured, skipping metrics submission")
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.metrics_url,
                    json=metrics.model_dump()
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to send metrics: {str(e)}")
            return False