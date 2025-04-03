import asyncio
import os
import time # To measure processing duration
from dotenv import load_dotenv
import redis.asyncio as redis
import pandas as pd
import numpy as np
import magic
from datetime import datetime, timedelta
from supabase import create_client, Client
import json
import re # Import regex for potential use
from arq import cron
from arq.connections import RedisSettings
import arq # For Arq pool creation

# Import analysis libraries
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer # Added CountVectorizer
from sklearn.feature_extraction import _stop_words # To get default stop words
from transformers import pipeline as hf_pipeline # Rename to avoid conflict
import torch # Ensure torch is available if using PyTorch models

# Load environment variables (essential for Supabase credentials)
load_dotenv()

# --- Supabase Client Initialization (using Service Role Key) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        # Initialize Supabase client synchronously during worker setup phase
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("INFO:WORKER: Supabase client initialized successfully.")
    except Exception as e:
        print(f"ERROR:WORKER: Failed to initialize Supabase client: {e}")
        supabase = None
else:
    print("WARN:WORKER: Supabase URL or Service Key not found. Database operations will fail.")

# --- NLP Model Initialization ---
# Load the sentiment analysis model once when the worker starts
# Use a simpler model for quicker loading if full accuracy isn't paramount initially
sentiment_pipeline = None
try:
    print("INFO:WORKER: Initializing sentiment analysis pipeline...")
    # Ensure device is set correctly (CPU might be more stable in some environments)
    device = 0 if torch.cuda.is_available() else -1 # Use GPU if available
    sentiment_pipeline = hf_pipeline(
        'sentiment-analysis',
        model='distilbert-base-uncased-finetuned-sst-2-english',
        device=device
    )
    print("INFO:WORKER: Sentiment analysis pipeline initialized.")
except Exception as e:
    print(f"ERROR:WORKER: Failed to initialize sentiment analysis pipeline: {e}")
    # Worker can still run, but sentiment analysis will fail

# --- Custom Stop Words --- (Define near imports or top of function)
CUSTOM_STOP_WORDS = set([
    'data', 'report', 'analysis', 'market', 'company', 'business', 'product', 'service',
    'new', 'like', 'use', 'time', 'need', 'people', 'information', 'update', 'trends',
    'insight', 'insights', 'analytics', 'research', 'growth', 'strategy', 'customer',
    'review', 'feedback', 'industry', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'monday', 'tuesday', 'wednesday',
    'thursday', 'friday', 'saturday', 'sunday', 'today', 'yesterday', 'tomorrow',
    'week', 'month', 'year', 'chart', 'figure', 'table', 'page', 'section',
    'inc', 'llc', 'corp', 'ltd', 'gmbh', 'co', 'the', 'and', 'is', 'are', 'in', 'it',
    # Add more domain-specific or general words to exclude
])

# --- Helper Functions ---

async def update_upload_status(upload_id: str, status: str, error: Optional[str] = None, extra_data: Optional[dict] = None):
    """Helper to update the status in the file_uploads table."""
    if not supabase:
        print(f"WARN:WORKER: Supabase client not available. Cannot update status for upload {upload_id}.")
        return

    update_payload = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "error_reason": error
    }
    if extra_data:
        update_payload.update(extra_data)

    try:
        await asyncio.to_thread(
            supabase.table("file_uploads") # Corrected table name
            .update(update_payload)
            .eq("id", upload_id) # Use upload_id (PK) for targeting
            .execute
        )
        print(f"INFO:WORKER: Updated status for upload {upload_id} to '{status}'.")
    except Exception as e:
        print(f"ERROR:WORKER: Failed to update status for upload {upload_id}: {e}")


# --- Main Task Function ---
async def process_uploaded_file(ctx, job_id: str, user_id: str, upload_id: str, file_path: str, original_filename: str):
    """
    Reads an uploaded file, performs analysis (stats, keywords, sentiment, time-series, correlation),
    stores results, updates DB status, and cleans up.
    """
    start_time = time.time()
    worker_id = ctx.get('worker_id', 'unknown')
    log_prefix = f"WORKER[{worker_id}] JOB[{job_id}] UPLOAD[{upload_id}] USER[{user_id}]:"
    print(f"{log_prefix} Starting processing for file '{original_filename}' ({file_path})")

    processed_data_payload = {
        "upload_id": upload_id,
        "user_id": user_id, # Store user_id for potential RLS/querying
        "summary_statistics": None,
        "extracted_keywords": None,
        "sentiment_scores": None,
        "time_series_analysis": None,
        "correlation_analysis": None,
        "processing_errors": None
    }
    analysis_errors = [] # Collect non-fatal errors during analysis

    try:
        # 0. Ensure Supabase client is available
        if not supabase:
             raise ConnectionError("Supabase client not initialized. Cannot proceed.")

        # 1. Update status to 'processing'
        await update_upload_status(upload_id, "processing")

        # 2. Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Temporary file does not exist: {file_path}")

        # 3. Read File using Pandas
        print(f"{log_prefix} Reading file...")
        df = None
        try:
            file_mime_type = magic.from_file(file_path, mime=True)
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()

            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type determined by extension: {file_extension}")

            if df.empty:
                 raise pd.errors.EmptyDataError("File is empty or could not be parsed by pandas.")
            print(f"{log_prefix} Read {len(df)} rows, {len(df.columns)} columns.")
        except Exception as read_err:
             print(f"{log_prefix} Error reading file: {read_err}")
             raise ValueError(f"Failed to read file content: {read_err}") from read_err

        # 4. Data Cleaning (Step 1a)
        print(f"{log_prefix} Cleaning data...")
        initial_rows = len(df)
        df.drop_duplicates(inplace=True)
        cleaned_rows = len(df)
        print(f"{log_prefix} Removed {initial_rows - cleaned_rows} duplicate rows.")
        # Basic missing value handling (example: fill numerical with median, categorical with mode)
        # More sophisticated handling might be needed based on data specifics
        for col in df.columns:
             if pd.api.types.is_numeric_dtype(df[col]):
                 if df[col].isnull().any():
                      median_val = df[col].median()
                      df[col].fillna(median_val, inplace=True)
                      # print(f"{log_prefix} Filled missing numerical values in '{col}' with median ({median_val}).") # Reduce log verbosity
             elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]): # Treat object as potential categorical/text
                 if df[col].isnull().any():
                      mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                      df[col].fillna(mode_val, inplace=True)
                      # print(f"{log_prefix} Filled missing categorical/text values in '{col}' with mode ('{mode_val}').") # Reduce log verbosity
        print(f"{log_prefix} Data cleaning finished.")

        # 5. Column Statistics (Step 1b)
        print(f"{log_prefix} Calculating column statistics...")
        summary_stats = {}
        for col in df.columns:
            col_stats = {"type": "unknown"}
            try:
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_stats["type"] = "numerical"
                    desc = df[col].describe()
                    col_stats.update({
                        "mean": desc.get("mean", None),
                        "median": desc.get("50%", None), # describe uses '50%' for median
                        "stddev": desc.get("std", None),
                        "min": desc.get("min", None),
                        "max": desc.get("max", None),
                        "25%": desc.get("25%", None),
                        "75%": desc.get("75%", None)
                        # Add outlier detection here if needed
                    })
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                     col_stats["type"] = "datetime"
                     col_stats["min"] = df[col].min().isoformat() if not df[col].isnull().all() else None
                     col_stats["max"] = df[col].max().isoformat() if not df[col].isnull().all() else None
                elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    # Could be categorical or free text
                    unique_count = df[col].nunique()
                    if unique_count / len(df) < 0.5 and unique_count < 1000: # Heuristic for categorical
                        col_stats["type"] = "categorical"
                        col_stats["unique_count"] = unique_count
                        value_counts = df[col].value_counts()
                        col_stats["mode"] = value_counts.idxmax() if not value_counts.empty else None
                        # Store top N frequencies to avoid huge JSON
                        col_stats["frequencies"] = value_counts.head(20).to_dict()
                    else:
                        col_stats["type"] = "text" # Assume free text if many unique values
                        col_stats["unique_count"] = unique_count
                summary_stats[col] = col_stats
            except Exception as stat_err:
                 print(f"{log_prefix} Error calculating stats for column '{col}': {stat_err}")
                 analysis_errors.append(f"StatsError ({col}): {stat_err}")
                 summary_stats[col] = {"type": "error", "detail": str(stat_err)}
        processed_data_payload["summary_statistics"] = summary_stats
        print(f"{log_prefix} Statistics calculated.")

        # 6. Keyword & Sentiment Analysis (Step 1c)
        print(f"{log_prefix} Performing keyword and sentiment analysis...")
        extracted_keywords = {}
        sentiment_scores = {}
        text_columns = [col for col, stats in summary_stats.items() if stats["type"] == "text"]

        if text_columns:
            # Combine text columns for analysis
            combined_text_series = df[text_columns].fillna('').agg(' '.join, axis=1)

            # Keyword Extraction (TF-IDF with custom stop words)
            try:
                # Combine default English stop words with custom ones
                default_stop_words = _stop_words.ENGLISH_STOP_WORDS
                combined_stop_words = list(default_stop_words.union(CUSTOM_STOP_WORDS))

                vectorizer = TfidfVectorizer(
                    stop_words=combined_stop_words,
                    max_features=1000, # Limit features
                    ngram_range=(1, 2) # Consider bi-grams too
                )
                tfidf_matrix = vectorizer.fit_transform(combined_text_series)
                feature_names = vectorizer.get_feature_names_out()
                vocabulary = vectorizer.vocabulary_

                # Get top N keywords based on overall TF-IDF score
                # Sum TF-IDF scores across all documents for each term
                term_scores = tfidf_matrix.sum(axis=0).A1
                top_keywords_indices = term_scores.argsort()[-20:][::-1] # Top 20 overall by summed score
                overall_top_keywords = [feature_names[i] for i in top_keywords_indices]
                extracted_keywords['overall_top_keywords'] = overall_top_keywords

                # Calculate Frequency of Top Keywords
                if overall_top_keywords:
                    print(f"{log_prefix} Calculating frequency for top {len(overall_top_keywords)} keywords...")
                    count_vectorizer = CountVectorizer(vocabulary=vocabulary) # Use exact same vocab
                    word_counts_matrix = count_vectorizer.fit_transform(combined_text_series)
                    term_counts = word_counts_matrix.sum(axis=0).A1
                    keyword_frequency = {feature_names[i]: int(term_counts[i]) for i in top_keywords_indices}
                    extracted_keywords['keyword_frequency'] = keyword_frequency
                    print(f"{log_prefix} Keyword frequencies calculated.")
                else:
                    extracted_keywords['keyword_frequency'] = {}

            except Exception as kw_err:
                 print(f"{log_prefix} Error during keyword extraction: {kw_err}")
                 analysis_errors.append(f"KeywordError: {kw_err}")
                 extracted_keywords['error'] = str(kw_err)
                 extracted_keywords['overall_top_keywords'] = []
                 extracted_keywords['keyword_frequency'] = {}
            processed_data_payload["extracted_keywords"] = extracted_keywords

            # Sentiment Analysis
            if sentiment_pipeline:
                try:
                    combined_text_list = combined_text_series.tolist()
                    # Process in batches if large dataset
                    batch_size = 128
                    all_sentiments = []
                    print(f"{log_prefix} Starting sentiment analysis batches...")
                    for i in range(0, len(combined_text_list), batch_size):
                         batch = combined_text_list[i:i+batch_size]
                         if batch: # Ensure batch is not empty
                            # Limit length of each item in batch for model
                            truncated_batch = [text[:512] for text in batch]
                            results = sentiment_pipeline(truncated_batch, truncation=True)
                            all_sentiments.extend(results)
                    print(f"{log_prefix} Finished sentiment analysis batches.")

                    # Aggregate sentiment scores
                    positive_score = sum(s['score'] for s in all_sentiments if s['label'] == 'POSITIVE')
                    negative_score = sum(s['score'] for s in all_sentiments if s['label'] == 'NEGATIVE')
                    total_count = len(all_sentiments)
                    if total_count > 0:
                        sentiment_scores['average'] = {
                            'positive': positive_score / total_count,
                            'negative': negative_score / total_count,
                            # Neutrality can be inferred or calculated if model provides it
                        }
                        sentiment_scores['overall_label'] = max(sentiment_scores['average'], key=sentiment_scores['average'].get)
                    else:
                         sentiment_scores['average'] = {'positive': 0, 'negative': 0}
                         sentiment_scores['overall_label'] = 'NEUTRAL'
                    # Could add per-column sentiment if needed
                except Exception as sent_err:
                    print(f"{log_prefix} Error during sentiment analysis: {sent_err}")
                    analysis_errors.append(f"SentimentError: {sent_err}")
                    sentiment_scores['error'] = str(sent_err)
            else:
                 print(f"{log_prefix} Sentiment pipeline not available, skipping analysis.")
                 sentiment_scores['error'] = "Pipeline not loaded"
            processed_data_payload["sentiment_scores"] = sentiment_scores
        else:
             print(f"{log_prefix} No text columns identified for keyword/sentiment analysis.")
             # Ensure payloads are set even if no text columns
             processed_data_payload["extracted_keywords"] = {'overall_top_keywords': [], 'keyword_frequency': {}}
             processed_data_payload["sentiment_scores"] = {'average': {'positive': 0, 'negative': 0}, 'overall_label': 'NEUTRAL'}
        print(f"{log_prefix} Keyword/Sentiment analysis finished.")

        # 7. Time Series Analysis (Step 1d) - Basic Example
        print(f"{log_prefix} Performing time series analysis...")
        time_series_analysis = {}
        datetime_cols = [col for col, stats in summary_stats.items() if stats["type"] == "datetime"]
        numerical_cols = [col for col, stats in summary_stats.items() if stats["type"] == "numerical"]

        if datetime_cols and numerical_cols:
            date_col = datetime_cols[0] # Use the first datetime column found
            # Ensure it's datetime type
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.sort_values(by=date_col)

            for val_col in numerical_cols:
                try:
                     # Example: Calculate rolling average (7-period)
                     rolling_mean = df.set_index(date_col)[val_col].rolling(window=7).mean()
                     time_series_analysis[f"{val_col}_rolling_mean_7d"] = rolling_mean.dropna().to_dict()
                     # Add more analyses: trend detection, seasonality etc.
                except Exception as ts_err:
                    print(f"{log_prefix} Error during time series analysis for '{val_col}': {ts_err}")
                    analysis_errors.append(f"TimeSeriesError ({val_col}): {ts_err}")
                    time_series_analysis[f"{val_col}_error"] = str(ts_err)
            processed_data_payload["time_series_analysis"] = time_series_analysis
        else:
            print(f"{log_prefix} Not enough datetime/numerical columns for time series analysis.")
        print(f"{log_prefix} Time series analysis finished.")

        # 8. Correlation Analysis (Step 1e)
        print(f"{log_prefix} Performing correlation analysis...")
        correlation_analysis = {}
        if datetime_cols and numerical_cols:
             try:
                 user_date_col = datetime_cols[0] # Assume first date col
                 user_metrics = numerical_cols # Use all numerical cols for now

                 # Fetch relevant market trends data from Supabase
                 min_date, max_date = df[user_date_col].min(), df[user_date_col].max()
                 print(f"{log_prefix} Querying market_trends between {min_date} and {max_date}")

                 trends_response = await asyncio.to_thread(
                     supabase.table("market_trends")
                     .select("trend_name, score, data_collected_at")
                     .gte("data_collected_at", min_date.isoformat())
                     .lte("data_collected_at", max_date.isoformat())
                     .execute
                 )

                 if trends_response.data:
                     trends_df = pd.DataFrame(trends_response.data)
                     trends_df['data_collected_at'] = pd.to_datetime(trends_df['data_collected_at'])
                     print(f"{log_prefix} Fetched {len(trends_df)} market trend records.")

                     # Pivot trends data for joining: date index, trend names as columns
                     trends_pivot = trends_df.pivot_table(index='data_collected_at', columns='trend_name', values='score')

                     # Align user data and trends data (e.g., resample to daily)
                     user_data_resampled = df.set_index(user_date_col)[user_metrics].resample('D').mean() # Example: daily mean
                     trends_resampled = trends_pivot.resample('D').mean() # Ensure trends also daily mean

                     # Combine and calculate correlation
                     combined_df = pd.concat([user_data_resampled, trends_resampled], axis=1).dropna()

                     if not combined_df.empty and len(combined_df) > 1: # Need at least 2 data points
                         correlation_matrix = combined_df.corr()
                         # Extract correlations between user metrics and trends
                         for user_col in user_metrics:
                             for trend_col in trends_resampled.columns:
                                 if user_col in correlation_matrix and trend_col in correlation_matrix:
                                      corr_value = correlation_matrix.loc[user_col, trend_col]
                                      # Store significant correlations (e.g., abs(corr) > 0.3)
                                      if abs(corr_value) > 0.3:
                                          correlation_analysis[f"{user_col}_vs_{trend_col}"] = {"correlation": corr_value}
                     else:
                          print(f"{log_prefix} Not enough overlapping data points for correlation after resampling.")

                 else:
                      print(f"{log_prefix} No relevant market trends data found for the period.")

             except Exception as corr_err:
                  print(f"{log_prefix} Error during correlation analysis: {corr_err}")
                  analysis_errors.append(f"CorrelationError: {corr_err}")
                  correlation_analysis["error"] = str(corr_err)
        else:
             print(f"{log_prefix} Not enough datetime/numerical columns for correlation analysis.")
        processed_data_payload["correlation_analysis"] = correlation_analysis
        print(f"{log_prefix} Correlation analysis finished.")

        # 9. Store Processed Results (Step 2)
        print(f"{log_prefix} Storing processed results...")
        processed_data_payload["processing_errors"] = analysis_errors if analysis_errors else None
        processed_data_payload["processed_at"] = datetime.utcnow().isoformat() # Add processed timestamp

        # Convert numpy types to standard python types for JSON serialization
        def convert_numpy_types(obj):
             if isinstance(obj, np.integer):
                 return int(obj)
             elif isinstance(obj, np.floating):
                 return float(obj)
             elif isinstance(obj, np.ndarray):
                 return obj.tolist()
             elif isinstance(obj, pd.Timestamp):
                 return obj.isoformat()
             elif isinstance(obj, dict):
                 return {k: convert_numpy_types(v) for k, v in obj.items()}
             elif isinstance(obj, list):
                 return [convert_numpy_types(i) for i in obj]
             return obj

        serializable_payload = convert_numpy_types(processed_data_payload)

        try:
            insert_processed_response = await asyncio.to_thread(
                supabase.table("processed_uploads")
                .insert(serializable_payload)
                .execute
            )
            # Basic check if insert seemed successful (Supabase client v1 might not raise exceptions easily)
            # A more robust check might query if the record exists afterwards
            # if not insert_processed_response.data: # This check might be unreliable
            #     raise Exception("Insert into processed_uploads returned no data")
            print(f"{log_prefix} Processed results stored successfully.")
        except Exception as insert_err:
             print(f"{log_prefix} Error storing processed results: {insert_err}")
             # This is a critical error for this job's purpose
             raise Exception(f"Failed to store processing results: {insert_err}") from insert_err

        # 10. Final Status Update (Completed)
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        print(f"{log_prefix} Processing completed successfully in {duration_ms}ms.")
        await update_upload_status(upload_id, "completed", extra_data={
            "row_count": len(df),
            "column_count": len(df.columns),
            "headers": json.dumps(list(df.columns)), # Store headers in original upload record too
        })
        final_status = "completed"

    except (ValueError, pd.errors.EmptyDataError, FileNotFoundError, ConnectionError) as specific_error:
        print(f"{log_prefix} ERROR - Processing failed due to specific error: {specific_error}")
        error_reason = str(specific_error)
        final_status = "failed"
        processed_data_payload["processing_errors"] = (analysis_errors or []) + [f"FatalError: {error_reason}"]
    except Exception as e:
        print(f"{log_prefix} ERROR - Unexpected failure: {type(e).__name__} - {e}")
        error_reason = f"Unexpected error during processing: {type(e).__name__}"
        final_status = "failed"
        processed_data_payload["processing_errors"] = (analysis_errors or []) + [f"FatalError: {error_reason}"]
    finally:
        # Update status/error if failed
        if final_status == "failed":
            try:
                await update_upload_status(upload_id, "failed", error=error_reason)
                # Attempt to save partial results if any analysis failed but didn't stop processing
                if supabase and processed_data_payload.get("summary_statistics"): # Check if some results exist
                    processed_data_payload["processed_at"] = datetime.utcnow().isoformat()
                    serializable_payload = convert_numpy_types(processed_data_payload)
                    print(f"{log_prefix} Attempting to save partial processed results on failure...")
                    await asyncio.to_thread(
                        supabase.table("processed_uploads")
                        .insert(serializable_payload)
                        .execute
                    )
                    print(f"{log_prefix} Partial processed results saved.")
            except Exception as final_update_err:
                print(f"{log_prefix} CRITICAL - Failed to update DB or save partial results on failure: {final_update_err}")

        # Cleanup - Always attempt to delete the temporary file
        try:
            if os.path.exists(file_path):
                print(f"{log_prefix} Cleaning up temporary file: {file_path}")
                os.remove(file_path)
                print(f"{log_prefix} Temporary file deleted.")
            else:
                 print(f"{log_prefix} Temporary file already removed or not found ({file_path}).")
        except OSError as e:
            print(f"{log_prefix} ERROR - Failed deleting temporary file {file_path}: {e}")

    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    print(f"{log_prefix} Processing finished with status: {final_status}. Duration: {duration_ms}ms")
    # Return dict can be used by Arq for job result info if needed
    return {"final_status": final_status, "job_id": job_id, "upload_id": upload_id, "duration_ms": duration_ms}


# --- Newsletter Functions (Keep as is for now) ---
async def generate_newsletter_content() -> Dict[str, Any]:
    """Generate newsletter content from recent insights and updates."""
    # ... (existing code) ...

async def send_newsletter(ctx) -> Dict[str, str]:
    """Send weekly newsletter to all subscribers."""
    # ... (existing code, but needs MailerSend integration instead of SendGrid) ...
    # TODO: Replace SendGrid with MailerSend using backend/services/email.py logic


# --- Arq Worker Settings ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

async def startup(ctx):
    worker_id = ctx.get('worker_id', 'unknown')
    print(f"INFO:WORKER[{worker_id}] Startup complete. Supabase available: {supabase is not None}. Sentiment pipeline available: {sentiment_pipeline is not None}")

async def shutdown(ctx):
    worker_id = ctx.get('worker_id', 'unknown')
    print(f"INFO:WORKER[{worker_id}] Shutdown complete.")

class WorkerSettings:
    """Settings for the ARQ worker."""
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379))
    )

    functions = [
        process_uploaded_file,
        send_newsletter
    ]

    # Run newsletter job every Monday at 9 AM UTC
    cron_jobs = [
        # cron(send_newsletter, weekday=1, hour=9, minute=0) # Temporarily disable cron job
    ]

    on_startup = startup
    on_shutdown = shutdown

# To run the worker, use the command:
# arq backend.worker.WorkerSettings