from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
import uuid

# Schema for individual data points in the Market Insights trend chart
class TrendDataPoint(BaseModel):
    collected_at: datetime
    score: float

# Schema for the overall response of the Market Insights section
class MarketInsightsResponse(BaseModel):
    trend_data: List[TrendDataPoint]
    top_trending_topic: str = Field(..., alias="topTrendingTopic")
    growth_rate: str = Field(..., alias="growthRate")
    mentionsData: Optional[dict] = None # Define more specific model later if needed
    growthData: Optional[dict] = None   # Define more specific model later if needed

# Add other dashboard-related schemas below as needed

# Schemas for Competitor Analysis
class CompetitorDataPoint(BaseModel):
    name: str
    value: int
    change: Optional[str] = None # 'up' or 'down'

class RecentChange(BaseModel):
    competitor: str
    change: str
    date: str

class CompetitorAnalysisResponse(BaseModel):
    competitorData: List[CompetitorDataPoint]
    recentChanges: List[RecentChange]

# Schemas for Sentiment Analysis
class SentimentTopic(BaseModel):
    name: str
    sentiment: int

class SentimentAnalysisResponse(BaseModel):
    positive: int
    neutral: int
    negative: int
    topics: List[SentimentTopic]

# Schemas for Recent Alerts
class AlertItem(BaseModel):
    # Let frontend handle icon/color based on type or title for now
    # icon_name: str 
    # color_class: str 
    type: str # e.g., "trend", "competitor", "sentiment"
    title: str
    description: str
    time: str

class RecentAlertsResponse(BaseModel):
    alerts: List[AlertItem]

class SentimentData(BaseModel):
    positive: float
    negative: float
    neutral: float
    keywords: List[str]

class AlertData(BaseModel):
    message: str
    level: str # e.g., 'info', 'warning', 'critical'
    timestamp: datetime

class MarketInsightData(BaseModel):
    trend_name: str
    growth_rate: float
    volume: int

class CompetitorData(BaseModel):
    name: str
    activity: str
    timestamp: datetime

# --- Upload Data Schemas ---

class UploadResult(BaseModel):
    """Schema for returning the status and results of a single file upload."""
    upload_id: uuid.UUID
    file_name: Optional[str] = None
    uploaded_at: datetime
    status: Optional[str] = None # e.g., 'queued', 'processing', 'completed', 'failed'
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    headers: Optional[List[str]] = None # Frontend expects a list
    error_reason: Optional[str] = None

    class Config:
        from_attributes = True # Enable ORM mode

class UploadResultList(BaseModel):
    """Schema for returning a list of upload results."""
    uploads: List[UploadResult] 