import httpx
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime

class RenderStatusMonitor:
    """Monitor Render.com service status."""
    
    def __init__(self):
        self.status_url = "https://status.render.com/api/v2/status.json"
        self.components_url = "https://status.render.com/api/v2/components.json"
        self.incidents_url = "https://status.render.com/api/v2/incidents.json"
        self._client = httpx.AsyncClient()

    async def get_overall_status(self) -> Dict[str, Any]:
        """Get the overall Render.com status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.status_url)
            response.raise_for_status()
            return response.json()

    async def get_component_status(self) -> Dict[str, Any]:
        """Get status of individual Render.com components."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.components_url)
            response.raise_for_status()
            return response.json()

    async def get_active_incidents(self) -> Dict[str, Any]:
        """Get any active incidents."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.incidents_url)
            response.raise_for_status()
            return response.json()

    async def monitor(self, callback, interval_seconds: int = 60):
        """
        Continuously monitor Render status and call the callback with updates.
        
        Args:
            callback: Async function to call with status updates
            interval_seconds: How often to check status
        """
        while True:
            try:
                status = await self.get_overall_status()
                components = await self.get_component_status()
                incidents = await self.get_active_incidents()
                
                await callback({
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status,
                    "components": components,
                    "incidents": incidents
                })
            except Exception as e:
                print(f"Error monitoring Render status: {e}")
            
            await asyncio.sleep(interval_seconds)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

# Example usage:
async def status_callback(status_update: Dict[str, Any]):
    """Example callback to handle status updates."""
    print(f"Render Status Update at {status_update['timestamp']}:")
    print(f"Overall Status: {status_update['status'].get('status', {}).get('description')}")
    
    if status_update.get('incidents', {}).get('incidents'):
        print("\nActive Incidents:")
        for incident in status_update['incidents']['incidents']:
            print(f"- {incident['name']}: {incident['status']}")

async def main():
    monitor = RenderStatusMonitor()
    try:
        await monitor.monitor(status_callback, interval_seconds=300)  # Check every 5 minutes
    finally:
        await monitor.close()

if __name__ == "__main__":
    asyncio.run(main()) 