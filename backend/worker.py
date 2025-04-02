import asyncio
import os
from dotenv import load_dotenv
import redis.asyncio as redis
import pandas as pd # For reading data files
import magic # For file type detection
from datetime import datetime # For date conversion
from supabase import create_client, Client # Import Supabase
import json # To handle JSON conversion for headers

# Load environment variables (essential for Supabase credentials)
load_dotenv()

# --- Supabase Client Initialization (using Service Role Key) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Ensure this is set in your .env!

# Check if Supabase credentials are provided
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("WARN:WORKER: Supabase URL or Service Key not found in environment variables. Database operations will fail.")
    supabase: Client | None = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("INFO:WORKER: Supabase client initialized successfully.")
    except Exception as e:
        print(f"ERROR:WORKER: Failed to initialize Supabase client: {e}")
        supabase: Client | None = None

# --- Task Function with Processing Logic ---
# Updated signature: job_id and user_id are now passed directly
async def process_uploaded_file(ctx, job_id: str, user_id: str, file_path: str, original_filename: str):
    """Reads an uploaded file, performs basic analysis, updates DB, and cleans up."""
    worker_id = ctx.get('worker_id', 'unknown') # Use ctx.get for safety
    log_prefix = f"WORKER[{worker_id}] JOB[{job_id}] USER[{user_id}] FILE[{original_filename}]:"
    print(f"{log_prefix} Starting processing for temp file {file_path}")

    analysis_result = {}
    error_reason = None
    final_status = "failed" # Default to failed

    try:
        # 0. Update status to 'processing'
        print(f"{log_prefix} Updating status to 'processing'...")
        if not supabase:
             raise ConnectionError("Supabase client not initialized. Cannot update job status.")
        await asyncio.to_thread(
            supabase.table("user_uploads")
            .update({"status": "processing", "updated_at": datetime.utcnow().isoformat()})
            .eq("job_id", job_id)
            .execute
        )
        print(f"{log_prefix} Status updated to 'processing'.")

        # Check if file exists before proceeding
        if not os.path.exists(file_path):
            print(f"{log_prefix} ERROR - File does not exist at path: {file_path}")
            raise FileNotFoundError(f"Temporary file does not exist: {file_path}")

        # 1. Determine File Type
        print(f"{log_prefix} Determining file type...")
        file_mime_type = magic.from_file(file_path, mime=True)
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()
        print(f"{log_prefix} Detected MIME type '{file_mime_type}', Extension '{file_extension}'")

        df = None
        # Slightly more robust type check
        is_csv = file_extension == '.csv' and ('csv' in file_mime_type or 'text' in file_mime_type)
        is_excel = file_extension in ['.xlsx', '.xls'] and \
                   ('excel' in file_mime_type or 'spreadsheet' in file_mime_type or \
                    'officedocument' in file_mime_type or ('zip' in file_mime_type and file_extension == '.xlsx'))

        # 2. Read the file using pandas
        if is_csv:
            print(f"{log_prefix} Reading as CSV...")
            df = pd.read_csv(file_path)
        elif is_excel:
            print(f"{log_prefix} Reading as Excel...")
            df = pd.read_excel(file_path)
        else:
            print(f"{log_prefix} ERROR - Unsupported file type. Ext: {file_extension}, MIME: {file_mime_type}")
            raise ValueError(f"Unsupported file type: Ext={file_extension}, MIME={file_mime_type}")

        if df.empty:
             print(f"{log_prefix} ERROR - File is empty after reading.")
             raise pd.errors.EmptyDataError("File is empty or could not be parsed.")

        print(f"{log_prefix} Successfully read {len(df)} rows and {len(df.columns)} columns.")

        # 3. Perform Basic Analysis
        print(f"{log_prefix} Performing basic analysis...")
        analysis_result = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "headers": list(df.columns)
        }
        print(f"{log_prefix} Analysis complete: {analysis_result}")

        # 4. Update Database on Success
        update_data = {
            "status": "completed",
            "row_count": analysis_result["row_count"],
            "column_count": analysis_result["column_count"],
            # Convert headers list to JSON string for Supabase jsonb column
            "headers": json.dumps(analysis_result["headers"]),
            "error_reason": None, # Clear any previous error
            "updated_at": datetime.utcnow().isoformat()
        }
        print(f"{log_prefix} Updating DB record as 'completed'...")
        response = await asyncio.to_thread(
            supabase.table("user_uploads")
            .update(update_data)
            .eq("job_id", job_id)
            .execute
        )
        # Optional: Check response for errors if needed
        # print(f"DB Update Response: {response}")
        final_status = "completed"
        print(f"{log_prefix} DB record updated to 'completed'.")

    except (ValueError, pd.errors.EmptyDataError, FileNotFoundError, ConnectionError) as specific_error:
        print(f"{log_prefix} ERROR - Processing failed: {specific_error}")
        error_reason = str(specific_error)
        final_status = "failed"
    except Exception as e:
        # Catch other potential errors
        print(f"{log_prefix} ERROR - Unexpected failure: {type(e).__name__} - {e}")
        error_reason = f"Unexpected error: {type(e).__name__}"
        final_status = "failed"
    finally:
        # 5. Update Database on Failure (if applicable)
        if final_status == "failed" and supabase and job_id and error_reason:
            try:
                update_data = {
                    "status": "failed",
                    "error_reason": error_reason,
                    "updated_at": datetime.utcnow().isoformat()
                }
                print(f"{log_prefix} Updating DB record as 'failed'. Reason: {error_reason}")
                await asyncio.to_thread(
                    supabase.table("user_uploads")
                    .update(update_data)
                    .eq("job_id", job_id)
                    .execute
                )
                print(f"{log_prefix} DB record updated to 'failed'.")
            except Exception as db_err:
                 print(f"{log_prefix} CRITICAL - Failed to update DB with failure status: {db_err}")

        # 6. Cleanup - Always attempt to delete the temporary file
        try:
            # Check existence again in case it was deleted by an error condition path already
            if os.path.exists(file_path):
                print(f"{log_prefix} Cleaning up temporary file: {file_path}")
                os.remove(file_path)
                print(f"{log_prefix} Temporary file deleted.")
            else:
                 print(f"{log_prefix} Temporary file already deleted or not found at path: {file_path}")
        except OSError as e:
            # Log error but don't raise, as the job result is more important
            print(f"{log_prefix} ERROR - Failed deleting temporary file {file_path}: {e}")

    # Worker function doesn't need to return detailed dict anymore, status is in DB
    print(f"{log_prefix} Processing finished with status: {final_status}")
    return {"final_status": final_status, "job_id": job_id} # Return simple status


# --- Arq Worker Settings ---

# Redis settings (no change needed)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

async def startup(ctx):
    worker_id = ctx.get('worker_id', 'unknown')
    # No need to create Supabase client here, it's global now
    print(f"INFO:WORKER[{worker_id}] Startup complete.")
    # Note: Original code had redis client creation here, but it's not used in process_uploaded_file
    # ctx['redis'] = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")

async def shutdown(ctx):
    worker_id = ctx.get('worker_id', 'unknown')
    print(f"INFO:WORKER[{worker_id}] Shutdown complete.")
    # if 'redis' in ctx and ctx['redis']:
    #     await ctx['redis'].close()

class WorkerSettings:
    """Defines settings for the Arq worker."""
    functions = [process_uploaded_file]
    redis_settings = redis.RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    on_startup = startup
    on_shutdown = shutdown
    keep_result = 3600 # Keep job results for 1 hour

# To run the worker, use the command:
# arq backend.worker.WorkerSettings 