from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from supabase import Client
import shutil # For saving files
import os # For creating directories and paths
import arq # For type hinting ArqRedis pool
import uuid # For generating job IDs
import json # For parsing headers from DB
from backend.schemas.dashboard import (
    MarketInsightsResponse,
    CompetitorAnalysisResponse,
    SentimentAnalysisResponse,
    RecentAlertsResponse,
    TrendDataPoint,
    CompetitorDataPoint,
    RecentChange,
    SentimentTopic,
    AlertItem,
    UploadResultList # Import the new list schema
)
from backend.database import get_db_client
from backend.security import get_current_user
from backend.worker import process_uploaded_file # Import the worker task
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

# Helper function to get Arq pool from request state
def get_arq_pool(request: Request) -> arq.ArqRedis:
    arq_pool = request.app.state.arq_pool
    if not arq_pool:
        raise HTTPException(status_code=500, detail="Task queue not available")
    return arq_pool

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

# --- New Endpoint for Fetching Upload Results ---
@router.get("/uploads", response_model=UploadResultList)
async def get_upload_results(
    db: Client = Depends(get_db_client),
    current_user: User = Depends(get_current_user)
):
    """Fetches the upload history for the currently logged-in user."""
    print(f"INFO: Fetching upload results for user_id: {current_user.id}")
    try:
        response = db.table('user_uploads')\
                     .select('id, job_id, original_filename, status, created_at, updated_at, row_count, column_count, headers, error_reason')\
                     .eq('user_id', current_user.id)\
                     .order('created_at', desc=True)\
                     .limit(50)\
                     .execute()

        if not response.data:
            print(f"INFO: No upload results found for user_id: {current_user.id}")
            return UploadResultList(uploads=[])

        # Parse headers from JSON string to list if not null
        for upload in response.data:
            if upload.get('headers') and isinstance(upload['headers'], str):
                try:
                    upload['headers'] = json.loads(upload['headers'])
                except json.JSONDecodeError:
                    print(f"WARN: Could not parse headers JSON for upload id {upload.get('id')}")
                    upload['headers'] = [] # Default to empty list on parse error
            elif upload.get('headers') is None:
                 upload['headers'] = [] # Default to empty list if null

        print(f"INFO: Found {len(response.data)} upload results for user_id: {current_user.id}")
        return UploadResultList(uploads=response.data)

    except Exception as e:
        print(f"ERROR: Failed fetching upload results for user_id {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching upload history.")

# --- Existing Upload Endpoint (Needs Modification) ---
# TODO: Modify this endpoint to insert into user_uploads and enqueue job
async def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validates file size, extension, and content type."""
    # 1. Size Check
    # Seek to the end to get the size, then back to the start
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return False, f"File size exceeds the limit of {MAX_FILE_SIZE // (1024 * 1024)}MB."

    # 2. Extension Check
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}."

    # 3. Content-Type Check
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        # Optionally, use python-magic for more robust type checking here if needed
        return False, f"Invalid file content type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}."

    return True, "File is valid."


@router.post("/upload")
async def upload_data(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Client = Depends(get_db_client), # Inject DB client
    arq_pool: arq.ArqRedis = Depends(get_arq_pool) # Inject Arq pool
):
    """
    Receives a file upload, validates it, saves it temporarily,
    creates a record in user_uploads with 'queued' status,
    and enqueues a background job for processing.
    """
    print(f"INFO: Received file upload request from user_id: {current_user.id}, filename: {file.filename}")

    # 1. Validate File
    print(f"INFO: Validating file: {file.filename} for user_id: {current_user.id}")
    is_valid, error_message = await validate_file(file)
    if not is_valid:
        print(f"WARN: Invalid file upload from user_id: {current_user.id}, filename: {file.filename}, reason: {error_message}")
        raise HTTPException(status_code=400, detail=error_message)
    print(f"INFO: File validation successful for: {file.filename}, user_id: {current_user.id}")

    # Reset file pointer after validation read it
    await file.seek(0)

    # 2. Save File Temporarily
    job_id = str(uuid.uuid4())
    # Use job_id in the filename to prevent collisions
    _, file_extension = os.path.splitext(file.filename)
    temp_file_name = f"{job_id}{file_extension}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, temp_file_name)
    print(f"INFO: Saving temporary file to: {temp_file_path} for job_id: {job_id}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"INFO: Temporary file saved successfully: {temp_file_path}")
    except Exception as e:
        print(f"ERROR: Failed to save temporary file {temp_file_path} for user_id {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
    finally:
        await file.close() # Ensure file handle is closed

    # 3. Create Initial Database Record
    print(f"INFO: Creating initial DB record for job_id: {job_id}, user_id: {current_user.id}")
    try:
        insert_data = {
            "job_id": job_id,
            "user_id": current_user.id,
            "original_filename": file.filename,
            "status": "queued", # Start with 'queued' status
            "temp_file_path": temp_file_path, # Store temp path for worker
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        response = db.table("user_uploads").insert(insert_data).execute()

        # Minimal check if insert appeared successful (adjust based on actual response)
        if not response.data:
            print(f"WARN: DB insert for job_id {job_id} might have failed (no data returned). Response: {response}")
            # Depending on strictness, you might raise an error here
            # For now, we proceed but log a warning

        print(f"INFO: Initial DB record created for job_id: {job_id}")

    except Exception as e:
        print(f"ERROR: Failed to create initial DB record for job_id {job_id}, user_id {current_user.id}: {e}")
        # Clean up the saved file if DB insert fails
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"INFO: Cleaned up temporary file due to DB error: {temp_file_path}")
            except OSError as rm_err:
                print(f"ERROR: Failed to cleanup temporary file {temp_file_path} after DB error: {rm_err}")
        raise HTTPException(status_code=500, detail="Failed to record upload job.")


    # 4. Enqueue Job
    print(f"INFO: Enqueuing background job for job_id: {job_id}")
    try:
        await arq_pool.enqueue_job(
            "process_uploaded_file",
            job_id=job_id,
            user_id=str(current_user.id), # Pass user ID
            file_path=temp_file_path,
            original_filename=file.filename
        )
        print(f"INFO: Job enqueued successfully for job_id: {job_id}")
    except Exception as e:
        print(f"ERROR: Failed to enqueue job for job_id {job_id}, user_id {current_user.id}: {e}")
        # Note: Consider how to handle enqueue failure.
        # Should the DB record be updated to 'failed'? Or attempt retry?
        # For now, just raise an error. The DB record will remain 'queued'.
        # A monitoring system could later identify stalled 'queued' jobs.
        raise HTTPException(status_code=500, detail="Failed to enqueue processing job.")

    return {"job_id": job_id, "status": "queued", "filename": file.filename}


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    request: Request, # Keep request to potentially access state if needed
    db: Client = Depends(get_db_client), # Inject DB client
    current_user: User = Depends(get_current_user)
):
    """Gets the status of a specific job from the user_uploads table."""
    print(f"INFO: Received status request for job_id: {job_id} from user_id: {current_user.id}")
    try:
        response = db.table("user_uploads") \
                     .select("status, error_reason, original_filename") \
                     .eq("job_id", job_id) \
                     .eq("user_id", current_user.id) \
                     .maybe_single() \
                     .execute()

        if not response.data:
            print(f"WARN: Job status not found for job_id: {job_id}, user_id: {current_user.id}")
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found or access denied.")

        job_data = response.data
        status = job_data.get("status", "unknown")
        error = job_data.get("error_reason")
        filename = job_data.get("original_filename", "N/A")

        print(f"INFO: Returning status '{status}' for job_id: {job_id}, user_id: {current_user.id}")
        
        # Return status and error message if failed
        response_data = {"job_id": job_id, "status": status, "filename": filename}
        if status == "failed" and error:
            response_data["message"] = error
        
        return response_data

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (like 404)
        raise http_exc
    except Exception as e:
        print(f"ERROR: Failed fetching status for job_id {job_id}, user_id {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching status for job {job_id}.")


# Placeholder for other dashboard endpoints (e.g., generating reports)
# @router.post("/generate-report")
# async def generate_report(params: dict, current_user: User = Depends(get_current_user)):
#     # Logic to generate a report based on user data
#     return {"message": "Report generation started"}