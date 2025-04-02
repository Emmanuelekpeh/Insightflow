# 1. Base Image
FROM python:3.11-slim

# 2. Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set Working Directory
WORKDIR /app

# 4. Install System Dependencies (if any - e.g., for python-magic)
# python-magic-bin includes its own binaries, but if using standard python-magic:
# RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*

# Install system dependencies for python-magic-bin
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python Dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code
# Copy the rest of the backend code
COPY . .

# 7. Expose Port (Render uses PORT env var, typically 10000)
EXPOSE 8000

# Use environment variable to determine which command to run
ENV SERVICE_TYPE=api

# Create an entrypoint script
RUN echo '#!/bin/sh\n\
if [ "$SERVICE_TYPE" = "worker" ]; then\n\
    exec arq backend.worker.WorkerSettings\n\
else\n\
    exec uvicorn backend.main:app --host 0.0.0.0 --port 8000\n\
fi' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
