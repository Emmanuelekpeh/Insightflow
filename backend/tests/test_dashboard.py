import pytest
from httpx import AsyncClient
from fastapi import status

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio

# --- Test Cases ---

async def test_get_sentiment_success(authenticated_client: AsyncClient):
    """Test successful retrieval of sentiment data (authenticated)."""
    response = await authenticated_client.get("/dashboard/sentiment")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed
    # e.g., assert "score" in response.json()

async def test_get_alerts_success(authenticated_client: AsyncClient):
    """Test successful retrieval of alerts data (authenticated)."""
    response = await authenticated_client.get("/dashboard/alerts")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed
    # e.g., assert isinstance(response.json(), list)

async def test_get_market_insights_success(authenticated_client: AsyncClient):
    """Test successful retrieval of market insights data (authenticated)."""
    response = await authenticated_client.get("/dashboard/market-insights")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed

async def test_get_competitor_analysis_success(authenticated_client: AsyncClient):
    """Test successful retrieval of competitor analysis data (authenticated)."""
    response = await authenticated_client.get("/dashboard/competitor-analysis")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed

# --- Test Cases for Unauthenticated Access ---

async def test_get_sentiment_unauthenticated(async_client: AsyncClient):
    """Test retrieving sentiment data without authentication."""
    response = await async_client.get("/dashboard/sentiment")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_alerts_unauthenticated(async_client: AsyncClient):
    """Test retrieving alerts data without authentication."""
    response = await async_client.get("/dashboard/alerts")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_market_insights_unauthenticated(async_client: AsyncClient):
    """Test retrieving market insights data without authentication."""
    response = await async_client.get("/dashboard/market-insights")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_competitor_analysis_unauthenticated(async_client: AsyncClient):
    """Test retrieving competitor analysis data without authentication."""
    response = await async_client.get("/dashboard/competitor-analysis")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 