import pytest
from httpx import AsyncClient
from fastapi import status
import io # For creating in-memory files
import os

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio

# --- Constants (mirroring those in dashboard.py) ---
# It's often better to import these from the source if possible,
# but defining them here makes the tests self-contained.
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# --- Test Cases ---

async def test_upload_success_csv(authenticated_client: AsyncClient):
    """Test successful upload of a CSV file."""
    # Create a dummy CSV file in memory
    csv_content = b"col1,col2\nval1,val2\nval3,val4"
    file_data = io.BytesIO(csv_content)
    files = {"file": ("test.csv", file_data, "text/csv")}
    
    response = await authenticated_client.post("/dashboard/upload", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "message" in response_data
    assert "job_id" in response_data
    assert response_data["filename"] == "test.csv"
    assert "queued for processing" in response_data["message"]
    # TODO: Optionally add direct check if job exists in Redis/Arq

async def test_upload_success_excel(authenticated_client: AsyncClient):
    """Test successful upload of an Excel file (.xlsx)."""
    # Create a dummy (empty) Excel file in memory - content doesn't matter for this test
    excel_content = b"PK\x05\x06" # Minimal valid zip file structure
    file_data = io.BytesIO(excel_content)
    files = {"file": ("test.xlsx", file_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    
    response = await authenticated_client.post("/dashboard/upload", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "job_id" in response_data
    assert response_data["filename"] == "test.xlsx"

async def test_upload_invalid_file_type(authenticated_client: AsyncClient):
    """Test uploading a file with an unsupported extension."""
    file_content = b"this is a text file"
    file_data = io.BytesIO(file_content)
    files = {"file": ("test.txt", file_data, "text/plain")}
    
    response = await authenticated_client.post("/dashboard/upload", files=files)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert "Invalid file extension" in response_data.get("detail", "")

async def test_upload_invalid_content_type(authenticated_client: AsyncClient):
    """Test uploading a file with an unsupported content type but valid extension."""
    file_content = b"this is actually plain text"
    file_data = io.BytesIO(file_content)
    # Mismatch: .csv extension but text/plain content type
    files = {"file": ("test.csv", file_data, "text/plain")}
    
    response = await authenticated_client.post("/dashboard/upload", files=files)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert "Invalid file content type" in response_data.get("detail", "")

async def test_upload_file_too_large(authenticated_client: AsyncClient):
    """Test uploading a file that exceeds the size limit."""
    # Create dummy data slightly larger than the limit
    large_content = b"a" * (MAX_FILE_SIZE + 1)
    file_data = io.BytesIO(large_content)
    files = {"file": ("large_file.csv", file_data, "text/csv")}
    
    response = await authenticated_client.post("/dashboard/upload", files=files)
    
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE # Or 400 based on exact exception handling
    response_data = response.json()
    assert "File size exceeds limit" in response_data.get("detail", "")

async def test_upload_no_file(authenticated_client: AsyncClient):
    """Test calling the upload endpoint without providing a file."""
    response = await authenticated_client.post("/dashboard/upload", files={}) # Empty files dict
    
    # FastAPI/Starlette should handle this before our endpoint logic
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 

async def test_get_job_status_success(authenticated_client: AsyncClient):
    """Test retrieving the status of a successfully enqueued job."""
    # 1. Upload a file to get a job ID
    csv_content = b"col1,col2\nval1,val2"
    file_data = io.BytesIO(csv_content)
    files = {"file": ("status_test.csv", file_data, "text/csv")}
    upload_response = await authenticated_client.post("/dashboard/upload", files=files)
    assert upload_response.status_code == status.HTTP_200_OK
    job_id = upload_response.json()["job_id"]
    assert job_id is not None

    # 2. Poll the status endpoint
    # Give Arq a moment to potentially register the job
    import asyncio
    await asyncio.sleep(0.1)
    
    status_response = await authenticated_client.get(f"/dashboard/jobs/{job_id}/status")
    assert status_response.status_code == status.HTTP_200_OK
    status_data = status_response.json()
    assert "job_id" in status_data
    assert status_data["job_id"] == job_id
    assert "status" in status_data
    # Possible statuses depend on whether a worker is running.
    # 'queued' is likely if no worker is present.
    # 'complete' if worker runs fast (unlikely for the dummy 5s sleep)
    # 'not_found' could occur if keep_result is short and check is slow
    assert status_data["status"] in ["queued", "processing", "completed", "deferred", "not_found"]

async def test_get_job_status_not_found(authenticated_client: AsyncClient):
    """Test retrieving the status of a non-existent job ID."""
    non_existent_job_id = "invalid-job-id-123"
    response = await authenticated_client.get(f"/dashboard/jobs/{non_existent_job_id}/status")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    assert "Job not found" in response_data.get("detail", "")

async def test_upload_unauthenticated(async_client: AsyncClient):
    """Test uploading a file without authentication."""
    csv_content = b"col1,col2\nval1,val2"
    file_data = io.BytesIO(csv_content)
    files = {"file": ("test_unauth.csv", file_data, "text/csv")}
    
    response = await async_client.post("/dashboard/upload", files=files)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_job_status_unauthenticated(async_client: AsyncClient):
    """Test retrieving job status without authentication."""
    # Need a job ID first, but we can just use a placeholder
    response = await async_client.get("/dashboard/jobs/any-job-id/status")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 