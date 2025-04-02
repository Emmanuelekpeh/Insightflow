import pytest
from httpx import AsyncClient
from fastapi import status

# Import the FastAPI app instance (adjust path if needed)
# Assuming your app instance is named 'app' in 'backend.main'
from backend.main import app 

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="module")
async def async_client():
    """Create an AsyncClient for making requests to the test app."""
    # Use 'async with' for proper lifespan management if your app uses it
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_read_root(async_client: AsyncClient):
    """Test the root endpoint ('/')."""
    response = await async_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to InsightFlow API"}

async def test_health_check(async_client: AsyncClient):
    """Test the health check endpoint ('/health')."""
    response = await async_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"} 