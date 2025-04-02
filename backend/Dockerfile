# 1. Base Image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install system dependencies for python-magic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements first for better caching
COPY backend/requirements.txt .

# 5. Upgrade pip and install dependencies
RUN pip install -r requirements.txt

# 6. Copy the application code
COPY backend/ .

# 7. Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app

# 8. Create entrypoint script
RUN echo '#!/bin/sh\n\
if [ "$SERVICE_TYPE" = "worker" ]; then\n\
    python worker.py\n\
else\n\
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
fi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# 9. Expose port
EXPOSE 8000

# 10. Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
