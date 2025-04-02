FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
# Install system dependencies needed for python-magic
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt

# Copy into a subdirectory to match the import structure
COPY . /app/backend/

ENV PYTHONPATH="${PYTHONPATH}:/app/backend"

# Run from the parent directory
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
