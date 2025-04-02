# 1. Base Image
FROM python:3.11-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements first for better caching
COPY backend/requirements.txt .

# 4. Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY backend/ .

# 6. Create entrypoint script
RUN echo '#!/bin/sh\n\
if [ "$SERVICE_TYPE" = "worker" ]; then\n\
    python worker.py\n\
else\n\
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
fi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# 7. Expose port
EXPOSE 8000

# 8. Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
