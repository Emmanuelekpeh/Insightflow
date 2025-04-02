import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, MagicMock # Import patching utilities
from datetime import datetime, timedelta # Import datetime for mocking timestamps
import uuid # For generating unique user IDs if needed

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio

# --- Test Cases ---

async def test_get_sentiment_success(authenticated_client: AsyncClient):
    """Test successful retrieval of sentiment data (authenticated)."""
    response = await authenticated_client.get("/api/dashboard/sentiment")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed
    response_data = response.json()
    assert "positive" in response_data
    assert "negative" in response_data
    assert "neutral" in response_data
    assert "topics" in response_data

async def test_get_alerts_success(authenticated_client: AsyncClient):
    """Test successful retrieval of alerts data (authenticated)."""
    response = await authenticated_client.get("/api/dashboard/alerts")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed
    response_data = response.json()
    assert "alerts" in response_data
    assert isinstance(response_data["alerts"], list)

async def test_get_market_insights_success(authenticated_client: AsyncClient):
    """Test successful retrieval of market insights data (authenticated)."""
    response = await authenticated_client.get("/api/dashboard/market-insights")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed
    response_data = response.json()
    assert "trend_data" in response_data
    assert "topTrendingTopic" in response_data
    assert "growthRate" in response_data

async def test_get_competitor_analysis_success(authenticated_client: AsyncClient):
    """Test successful retrieval of competitor analysis data (authenticated)."""
    response = await authenticated_client.get("/api/dashboard/competitor-analysis")
    assert response.status_code == status.HTTP_200_OK
    # Add more specific assertions about the response data if needed
    response_data = response.json()
    assert "competitorData" in response_data
    assert "recentChanges" in response_data

# --- Test Cases for Recent Alerts ---

async def test_get_recent_alerts_no_data(authenticated_client: AsyncClient):
    """Test retrieving alerts when no processed data is available."""
    
    # Mock the database response for no data
    mock_execute = MagicMock()
    mock_execute.data = None # Simulate maybe_single() returning None
    
    # Patch the chain of Supabase calls within the endpoint's scope
    with patch('backend.routers.dashboard.db.table') as mock_table:
        # Configure the mock to return our desired result when execute() is called
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        
        response = await authenticated_client.get("/api/dashboard/recent-alerts") # Corrected endpoint path

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "alerts" in response_data
    assert isinstance(response_data["alerts"], list)
    assert len(response_data["alerts"]) == 0 # Expect no alerts when no data

async def test_get_recent_alerts_positive_sentiment(authenticated_client: AsyncClient):
    """Test generating a positive sentiment alert."""
    sentiment_score = 0.85
    processed_at_time = datetime.utcnow() - timedelta(minutes=10)
    mock_data = {
        "sentiment_scores": {"average": {"positive": sentiment_score, "negative": 0.1}},
        "extracted_keywords": {"overall_top_keywords": ["great", "fantastic", "excellent"], "keyword_frequency": {}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "alerts" in response_data
    alerts = response_data["alerts"]
    assert len(alerts) > 0

    # Check for the positive sentiment alert
    sentiment_alert_found = False
    for alert in alerts:
        if alert["type"] == "sentiment" and "Positive Sentiment Spike" in alert["title"]:
            sentiment_alert_found = True
            assert f"Score: {sentiment_score:.2f}" in alert["description"]
            assert "10m ago" in alert["time"] # Check relative time formatting
            break
    assert sentiment_alert_found, "Positive sentiment alert not found"

    # Also check for the fallback 'trend' alert (since no critical keywords)
    trend_alert_found = False
    for alert in alerts:
        if alert["type"] == "trend" and "Top Topic Mention" in alert["title"]:
             trend_alert_found = True
             assert "Great" in alert["description"] # Check it picked the top keyword
             break
    assert trend_alert_found, "Fallback trend alert not found"

async def test_get_recent_alerts_negative_sentiment(authenticated_client: AsyncClient):
    """Test generating a negative sentiment alert."""
    sentiment_score = 0.6 # Test with negative score magnitude
    processed_at_time = datetime.utcnow() - timedelta(hours=2)
    mock_data = {
        "sentiment_scores": {"average": {"positive": 0.1, "negative": sentiment_score}},
        "extracted_keywords": {"overall_top_keywords": ["issue", "problem", "failed"], "keyword_frequency": {}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "alerts" in response_data
    alerts = response_data["alerts"]
    assert len(alerts) > 0

    # Check for the negative sentiment alert
    sentiment_alert_found = False
    for alert in alerts:
        if alert["type"] == "sentiment" and "Negative Sentiment Spike" in alert["title"]:
            sentiment_alert_found = True
            assert f"Score: {sentiment_score:.2f}" in alert["description"]
            assert "2h ago" in alert["time"] # Check relative time formatting
            break
    assert sentiment_alert_found, "Negative sentiment alert not found"

    # Also check for the fallback 'trend' alert
    trend_alert_found = False
    for alert in alerts:
        if alert["type"] == "trend" and "Top Topic Mention" in alert["title"]:
             trend_alert_found = True
             assert "Issue" in alert["description"] # Check it picked the top keyword
             break
    assert trend_alert_found, "Fallback trend alert not found"

async def test_get_recent_alerts_critical_keyword(authenticated_client: AsyncClient):
    """Test generating a keyword alert when a critical keyword is present."""
    critical_kw = "risk"
    processed_at_time = datetime.utcnow() - timedelta(days=1)
    mock_data = {
        "sentiment_scores": {"average": {"positive": 0.4, "negative": 0.1}}, # Neutral sentiment
        "extracted_keywords": {"overall_top_keywords": [critical_kw, "analysis", "report"], "keyword_frequency": {critical_kw: 3}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "alerts" in response_data
    alerts = response_data["alerts"]
    assert len(alerts) > 0 # Should have at least the keyword alert

    # Check for the critical keyword alert
    keyword_alert_found = False
    for alert in alerts:
        if alert["type"] == "keyword" and "Critical Keyword Mention" in alert["title"]:
            keyword_alert_found = True
            assert f"Keyword '{critical_kw}' found" in alert["description"]
            assert "1d ago" in alert["time"] # Check relative time formatting
            break
    assert keyword_alert_found, "Critical keyword alert not found"

    # Ensure the fallback 'trend' alert is NOT present
    trend_alert_found = False
    for alert in alerts:
        if alert["type"] == "trend" and "Top Topic Mention" in alert["title"]:
             trend_alert_found = True
             break
    assert not trend_alert_found, "Fallback trend alert should be suppressed when a critical keyword alert exists"

async def test_get_recent_alerts_no_specific_alerts(authenticated_client: AsyncClient):
    """Test generating only the fallback trend alert when no other conditions are met."""
    processed_at_time = datetime.utcnow() - timedelta(days=3)
    mock_data = {
        "sentiment_scores": {"average": {"positive": 0.3, "negative": 0.1}}, # Below thresholds
        "extracted_keywords": {"overall_top_keywords": ["meeting", "notes", "update"], "keyword_frequency": {}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "alerts" in response_data
    alerts = response_data["alerts"]
    assert len(alerts) == 1, "Expected only one alert (the fallback trend)"

    # Check that the only alert is the fallback 'trend' alert
    assert alerts[0]["type"] == "trend"
    assert "Top Topic Mention" in alerts[0]["title"]
    assert "Meeting" in alerts[0]["description"] # Check it picked the top keyword
    assert "3d ago" in alerts[0]["time"]

async def test_get_recent_alerts_multiple_alerts(authenticated_client: AsyncClient):
    """Test generating multiple alerts (sentiment + keyword) from one entry."""
    sentiment_score = 0.7 # High negative score
    critical_kw = "critical"
    processed_at_time = datetime.utcnow() - timedelta(minutes=5)
    mock_data = {
        "sentiment_scores": {"average": {"positive": 0.1, "negative": sentiment_score}},
        "extracted_keywords": {"overall_top_keywords": ["analysis", critical_kw, "report"], "keyword_frequency": {critical_kw: 2}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "alerts" in response_data
    alerts = response_data["alerts"]
    # Should have exactly 2 alerts: sentiment and keyword
    assert len(alerts) == 2, f"Expected 2 alerts, got {len(alerts)}"

    # Check for the negative sentiment alert
    sentiment_alert_found = False
    for alert in alerts:
        if alert["type"] == "sentiment" and "Negative Sentiment Spike" in alert["title"]:
            sentiment_alert_found = True
            assert f"Score: {sentiment_score:.2f}" in alert["description"]
            assert "5m ago" in alert["time"]
            break
    assert sentiment_alert_found, "Negative sentiment alert not found"

    # Check for the critical keyword alert
    keyword_alert_found = False
    for alert in alerts:
        if alert["type"] == "keyword" and "Critical Keyword Mention" in alert["title"]:
            keyword_alert_found = True
            assert f"Keyword '{critical_kw}' found" in alert["description"]
            assert "5m ago" in alert["time"]
            break
    assert keyword_alert_found, "Critical keyword alert not found"

    # Ensure the fallback 'trend' alert is NOT present
    trend_alert_found = False
    for alert in alerts:
        if alert["type"] == "trend":
             trend_alert_found = True
             break
    assert not trend_alert_found, "Fallback trend alert should be suppressed when other alerts exist"

async def test_get_recent_alerts_positive_threshold(authenticated_client: AsyncClient):
    """Test generating a positive sentiment alert exactly at the threshold."""
    sentiment_score = 0.7 # Exact threshold
    processed_at_time = datetime.utcnow() - timedelta(minutes=1)
    mock_data = {
        "sentiment_scores": {"average": {"positive": sentiment_score, "negative": 0.1}},
        "extracted_keywords": {"overall_top_keywords": ["ok", "good", "average"], "keyword_frequency": {}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    alerts = response_data["alerts"]
    
    # Check for the positive sentiment alert
    sentiment_alert_found = False
    for alert in alerts:
        if alert["type"] == "sentiment" and "Positive Sentiment Spike" in alert["title"]:
            sentiment_alert_found = True
            assert f"Score: {sentiment_score:.2f}" in alert["description"]
            assert "1m ago" in alert["time"] 
            break
    assert sentiment_alert_found, "Positive sentiment alert should be generated at the threshold"

async def test_get_recent_alerts_negative_threshold(authenticated_client: AsyncClient):
    """Test generating a negative sentiment alert exactly at the threshold."""
    sentiment_score = 0.5 # Exact threshold for negative magnitude
    processed_at_time = datetime.utcnow() - timedelta(seconds=30)
    mock_data = {
        "sentiment_scores": {"average": {"positive": 0.1, "negative": sentiment_score}},
        "extracted_keywords": {"overall_top_keywords": ["concern", "slow", "wait"], "keyword_frequency": {}},
        "processed_at": processed_at_time.isoformat()
    }
    
    mock_execute = MagicMock()
    mock_execute.data = mock_data
    
    with patch('backend.routers.dashboard.db.table') as mock_table:
        mock_table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.maybe_single.return_value.execute.return_value = mock_execute
        response = await authenticated_client.get("/api/dashboard/recent-alerts")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    alerts = response_data["alerts"]

    # Check for the negative sentiment alert
    sentiment_alert_found = False
    for alert in alerts:
        if alert["type"] == "sentiment" and "Negative Sentiment Spike" in alert["title"]:
            sentiment_alert_found = True
            assert f"Score: {sentiment_score:.2f}" in alert["description"]
            assert "just now" in alert["time"] # Check relative time formatting
            break
    assert sentiment_alert_found, "Negative sentiment alert should be generated at the threshold"

# --- Test Cases for Unauthenticated Access ---

async def test_get_sentiment_unauthenticated(async_client: AsyncClient):
    """Test retrieving sentiment data without authentication."""
    response = await async_client.get("/api/dashboard/sentiment")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_alerts_unauthenticated(async_client: AsyncClient):
    """Test retrieving alerts data without authentication."""
    response = await async_client.get("/api/dashboard/alerts")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_market_insights_unauthenticated(async_client: AsyncClient):
    """Test retrieving market insights data without authentication."""
    response = await async_client.get("/api/dashboard/market-insights")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_competitor_analysis_unauthenticated(async_client: AsyncClient):
    """Test retrieving competitor analysis data without authentication."""
    response = await async_client.get("/api/dashboard/competitor-analysis")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 