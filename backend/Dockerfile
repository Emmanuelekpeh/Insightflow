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

# Create and add the download script
COPY backend/scripts/download_model.py /tmp/download_model.py
RUN python /tmp/download_model.py

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
