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

# 5. Install Python Dependencies
# Copy only requirements first to leverage Docker cache
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code
# Copy the rest of the backend code
COPY ./backend /app/backend

# 7. Expose Port (Render uses PORT env var, typically 10000)
EXPOSE 10000

# 8. Default Command (Will be overridden by Render start command)
# Default to running the web server
# Note: Render injects $PORT, so we use that in the start command in render.yaml
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
