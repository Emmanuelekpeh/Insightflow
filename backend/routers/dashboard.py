from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from supabase import Client
import shutil # For saving files
import os # For creating directories and paths
import arq # For type hinting ArqRedis pool
from backend.schemas.dashboard import (
    MarketInsightsResponse,
    CompetitorAnalysisResponse,
    SentimentAnalysisResponse,
    RecentAlertsResponse,
    TrendDataPoint,
    CompetitorDataPoint,
    RecentChange,
    SentimentTopic,
    AlertItem
)
from backend.database import get_db_client
from backend.security import get_current_user
from gotrue.types import User
from datetime import datetime
from typing import List

# Define the path for temporary uploads
TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
# Ensure the directory exists
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Constants for file validation
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (Supabase Free Plan limit)
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

# Placeholder for dashboard data endpoints
@router.get("/")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    # TODO: Replace with actual data fetching and processing
    return {"message": f"Dashboard summary for user {current_user.email}"}

# Example endpoint for market insights data (matching frontend component)
@router.get("/market-insights", response_model=MarketInsightsResponse)
async def get_market_insights(db: Client = Depends(get_db_client), current_user: User = Depends(get_current_user)):
    try:
        # Fetch the latest 12 trend data points, ordered by date
        response = db.table('market_trends')\
                     .select('data_collected_at, trend_score, keyword')\
                     .order('data_collected_at', desc=True)\
                     .limit(12)\
                     .execute()

        if not response.data:
            # Handle case where no data is returned
            return MarketInsightsResponse(
                trend_data=[],
                topTrendingTopic="No data available",
                growthRate="N/A"
            )
        
        # Process fetched data into TrendDataPoint objects
        # Note: Supabase returns datetime strings, need parsing if not automatic
        processed_trend_data = [
            TrendDataPoint(
                collected_at=datetime.fromisoformat(item['data_collected_at']),
                score=item['trend_score']
            )
            for item in response.data
        ]
        # Reverse the list so the chart shows chronological order (oldest first)
        processed_trend_data.reverse()

        # --- Placeholder logic for top topic and growth rate ---
        # Use the keyword from the most recent data point as the top topic
        top_topic = response.data[0]['keyword'] if response.data else "N/A"
        # Fixed growth rate for now
        growth_rate = "+15.0%" 
        # -----------------------------------------------------
        
        return MarketInsightsResponse(
            trend_data=processed_trend_data,
            topTrendingTopic=top_topic, # FastAPI handles the alias on serialization
            growthRate=growth_rate
        )

    except Exception as e:
        print(f"Error fetching market insights for user {current_user.id}: {e}")
        # Raise an HTTP exception if there's a database error
        raise HTTPException(status_code=500, detail="Error fetching market insights data.")

# Endpoint for Competitor Analysis
@router.get("/competitor-analysis", response_model=CompetitorAnalysisResponse)
async def get_competitor_analysis(db: Client = Depends(get_db_client), current_user: User = Depends(get_current_user)):
    try:
        # --- Fetch Competitor Data --- 
        # Fetch first 5 competitors for the chart (can be refined later)
        competitors_response = db.table('competitors')\
                                 .select('competitor_id, name')\
                                 .limit(5)\
                                 .execute()

        competitor_data_points = []
        if competitors_response.data:
             # Use placeholder value for score, as it's not in the DB schema
            competitor_data_points = [
                CompetitorDataPoint(name=comp['name'], value=70.0) # Placeholder value
                for comp in competitors_response.data
            ]
            # Add "Your Company" placeholder if needed for comparison
            # competitor_data_points.insert(0, CompetitorDataPoint(name="Your Company", value=85.0)) 

        # --- Fetch Recent Changes --- 
        # Fetch latest 3 activities, joining with competitors table for name
        activities_response = db.table('competitor_activities')\
                                .select('description, detected_at, competitors(name)')\
                                .order('detected_at', desc=True)\
                                .limit(3)\
                                .execute()

        recent_changes_list = []
        if activities_response.data:
            recent_changes_list = [
                RecentChange(
                    competitor=activity['competitors']['name'], 
                    change=activity['description'],\
                    # Format timestamp (example: "2 days ago", needs proper logic)
                    date=f"{activity['detected_at'][:10]}" # Simple date format for now
                )\
                for activity in activities_response.data if activity.get('competitors') # Check if competitor join worked
            ]

        return CompetitorAnalysisResponse(\
            competitorData=competitor_data_points,\
            recentChanges=recent_changes_list\
        )

    except Exception as e:
        print(f"Error fetching competitor analysis for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching competitor analysis data.")

# Endpoint for Sentiment Analysis
@router.get("/sentiment-analysis", response_model=SentimentAnalysisResponse)
async def get_sentiment_analysis(db: Client = Depends(get_db_client), current_user: User = Depends(get_current_user)):
    try:
        # Fetch latest 100 sentiment records FOR THE CURRENT USER
        sentiment_response = db.table('sentiments')\
                               .select('sentiment_score, keyword, mention_count')\
                               .eq('user_id', current_user.id)\
                               .order('data_collected_at', desc=True)\
                               .limit(100)\
                               .execute()

        if not sentiment_response.data:
            # Handle case with no data
            return SentimentAnalysisResponse(
                positive=0, neutral=0, negative=0, topics=[]
            )

        records = sentiment_response.data
        total_records = len(records)

        # Calculate overall sentiment breakdown
        pos_count = 0
        neg_count = 0
        neu_count = 0
        topic_sentiments = {}
        topic_counts = {}

        for record in records:
            score = record['sentiment_score']
            keyword = record['keyword']
            
            # Overall counts
            if score > 0.1:
                pos_count += 1
            elif score < -0.1:
                neg_count += 1
            else:
                neu_count += 1
            
            # Topic aggregation
            if keyword:
                if keyword not in topic_sentiments:
                    topic_sentiments[keyword] = 0.0
                    topic_counts[keyword] = 0
                topic_sentiments[keyword] += score
                topic_counts[keyword] += 1

        # Calculate percentages
        positive_perc = round((pos_count / total_records) * 100) if total_records > 0 else 0
        negative_perc = round((neg_count / total_records) * 100) if total_records > 0 else 0
        neutral_perc = 100 - positive_perc - negative_perc # Ensure it sums to 100

        # Process topics - calculate average and get top 4 by count
        processed_topics = []
        # Sort topics by count (descending) to get the most frequent
        sorted_topics = sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)
        
        for topic, count in sorted_topics[:4]: # Get top 4 topics
            avg_score = topic_sentiments[topic] / count
            # Convert avg score (-1 to 1) to percentage (0 to 100) for display
            sentiment_perc = round(((avg_score + 1) / 2) * 100) 
            processed_topics.append(SentimentTopic(name=topic, sentiment=sentiment_perc))

        return SentimentAnalysisResponse(
            positive=positive_perc,
            neutral=neutral_perc,
            negative=negative_perc,
            topics=processed_topics
        )

    except Exception as e:
        print(f"Error fetching sentiment analysis for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching sentiment analysis data.")

# Endpoint for Recent Alerts
@router.get("/recent-alerts", response_model=RecentAlertsResponse)
async def get_recent_alerts(db: Client = Depends(get_db_client), current_user: User = Depends(get_current_user)):
    try:
        # Fetch latest 5 alerts FOR THE CURRENT USER, ordered by time sent
        response = db.table('alerts')\
                     .select('alert_type, message, sent_at')\
                     .eq('user_id', current_user.id)\
                     .order('sent_at', desc=True)\
                     .limit(5)\
                     .execute()

        if not response.data:
            return RecentAlertsResponse(alerts=[])

        processed_alerts = []
        for alert in response.data:
            # Create a simple title based on type
            title = f"{alert['alert_type'].replace('_', ' ').title()} Alert"
            # Format timestamp (example: "HH:MM DD/MM/YYYY", needs proper logic)
            try:
                timestamp = datetime.fromisoformat(alert['sent_at'])
                time_str = timestamp.strftime('%H:%M %d/%m/%Y') # Example format
            except:
                time_str = "Invalid date"

            processed_alerts.append(
                AlertItem(
                    type=alert['alert_type'],
                    title=title,
                    description=alert['message'],
                    time=time_str
                )
            )

        return RecentAlertsResponse(alerts=processed_alerts)

    except Exception as e:
        print(f"Error fetching recent alerts for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching recent alerts.")

async def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate the uploaded file against size and type restrictions.
    
    Size Limits:
    - Free Plan: 50MB
    - Pro/Team Plans: Up to 50GB
    - Enterprise: Custom limits
    
    Returns:
    - tuple[bool, str]: (is_valid, error_message)
    """
    # Check file size
    contents = await file.read()
    await file.seek(0)  # Reset file pointer
    
    size_mb = len(contents) / (1024 * 1024)
    if len(contents) > MAX_FILE_SIZE:
        return False, (
            f"File too large ({size_mb:.1f}MB). Maximum size is {MAX_FILE_SIZE/1024/1024:.1f}MB. "
            "Upgrade your plan for larger file uploads."
        )

    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return False, (
            f"Invalid file type: {file.content_type}. "
            f"Allowed types: CSV, Excel files"
        )

    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, (
            f"Invalid file extension: {ext}. "
            f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return True, "", contents  # Return contents to avoid reading twice

@router.post("/upload")
async def upload_data(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a file for processing."""
    # Validate the file
    is_valid, error_message = await validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    try:
        # Create temp_uploads directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)

        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ('.', '-', '_')).rstrip()
        temp_file_path = os.path.join(temp_dir, f"{timestamp}_{current_user.id[:8]}_{safe_filename}")

        # Save the uploaded file
        print(f"Saving uploaded file to: {temp_file_path}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File saved successfully")

        # Get the Arq pool
        arq_pool = request.app.state.arq_pool
        if not arq_pool:
            raise HTTPException(status_code=500, detail="Background task queue not available")

        # Enqueue the processing job
        print(f"Enqueuing job process_uploaded_file for {temp_file_path}")
        job = await arq_pool.enqueue_job(
            'process_uploaded_file',
            temp_file_path,
            str(current_user.id)
        )
        print(f"Job enqueued with ID: {job.job_id}")

        if not job:
            raise HTTPException(status_code=500, detail="Failed to enqueue processing task")

        return {
            "status": "accepted",
            "message": "File uploaded successfully and queued for processing",
            "job_id": job.job_id,
            "filename": file.filename,
            "size": len(contents),
            "content_type": file.content_type
        }

    except Exception as e:
        print(f"Error during file upload for user {current_user.id}: {e}")
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass  # Already being handled by the main error
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await file.close()

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a background job."""
    try:
        # Get the Arq pool from application state
        arq_pool = request.app.state.arq_pool
        if not arq_pool:
            raise HTTPException(status_code=500, detail="Background task queue not available")

        # Try to get the job result
        job = await arq_pool.get_job_result(job_id)
        
        if job is None:
            # Job not found or expired from Redis
            return {
                "status": "not_found",
                "message": "Job not found or result expired"
            }

        # Check if job is finished
        if isinstance(job, dict):
            # Job is complete, return the result
            return {
                "status": "completed",
                "result": job
            }
        
        # Job exists but not complete
        job_info = await arq_pool.job_info(job_id)
        if not job_info:
            return {
                "status": "not_found",
                "message": "Job info not available"
            }

        # Map job status to something frontend-friendly
        status_map = {
            "deferred": "queued",
            "queued": "queued", 
            "in_progress": "processing",
            "complete": "completed",
            "failed": "failed"
        }
        
        return {
            "status": status_map.get(job_info.status, "unknown"),
            "message": f"Job is {job_info.status}"
        }

    except Exception as e:
        print(f"Error checking job status for {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking job status: {str(e)}"
        )

# Add more endpoints for Competitor Analysis, Sentiment Analysis, Recent Alerts etc. here
# e.g., @router.get("/competitor-analysis") ...
# e.g., @router.get("/sentiment-analysis") ...
# e.g., @router.get("/recent-alerts") ...