FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy into a subdirectory to match the import structure
COPY . /app/backend/

ENV PYTHONPATH="${PYTHONPATH}:/app/backend"

# Run from the parent directory
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
