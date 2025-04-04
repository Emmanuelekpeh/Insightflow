FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create cache directory for transformers with proper permissions
RUN mkdir -p /tmp/transformers_cache && chmod 777 /tmp/transformers_cache

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model during build with explicit cache directory and error handling
ENV TRANSFORMERS_CACHE="/tmp/transformers_cache"
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# Download model with retries and verbose output
RUN python -c '\
try:\
    from transformers import pipeline;\
    import os;\
    print("INFO: Cache directory:", os.getenv("TRANSFORMERS_CACHE"));\
    print("INFO: Downloading sentiment analysis model...");\
    for attempt in range(3):\
        try:\
            model = pipeline(\
                "sentiment-analysis",\
                model="distilbert-base-uncased-finetuned-sst-2-english",\
                device=-1,\
                cache_dir="/tmp/transformers_cache"\
            );\
            print("INFO: Testing model with sample text...");\
            result = model("This is a test sentence.");\
            print(f"INFO: Model test result: {result}");\
            print("INFO: Model download and test successful!");\
            break;\
        except Exception as e:\
            print(f"WARNING: Attempt {attempt + 1} failed: {e}");\
            if attempt == 2:\
                raise;\
            import time;\
            time.sleep(5);\
except Exception as e:\
    print(f"ERROR: Model download/test failed: {e}");\
    raise e;\
'

# Copy application code
COPY . /app/backend/

# Set environment variables
ENV PYTHONPATH="/app/backend"

# Run command based on SERVICE_TYPE
CMD if [ "$SERVICE_TYPE" = "worker" ]; then \
        arq backend.worker.WorkerSettings; \
    else \
        python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000; \
    fi
