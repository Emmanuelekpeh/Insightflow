# 1. Base Image
FROM python:3.11-slim

# 2. Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set Working Directory
WORKDIR /app

# 4. Install System Dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code
COPY backend/ .

# 7. Expose Port
EXPOSE 8000

# Create a startup script that runs both the API and worker
RUN echo '#!/bin/sh\n\
# Start the worker in the background\n\
arq backend.worker.WorkerSettings & \n\
\n\
# Start the API server\n\
uvicorn backend.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh \
    && chmod +x /app/start.sh

# Use the startup script
CMD ["/app/start.sh"]
