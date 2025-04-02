import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

# Import the FastAPI app instance
from backend.main import app # Assuming app is accessible like this


@pytest.fixture(scope="session")
def event_loop():
    """Force pytest-asyncio to use the same event loop for all tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def async_client():
    """Provides an asynchronous test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


def generate_test_user():
    """Generates unique user credentials for testing."""
    unique_id = str(uuid.uuid4()) # Generate a unique ID
    return {
        "email": f"testuser_{unique_id}@example.com",
        "password": "strongPassword123",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture(scope="function") # Use function scope to get a fresh user/token per test
async def authenticated_client(async_client: AsyncClient):
    """Signs up and logs in a user, returns an authenticated client."""
    user_data = generate_test_user()
    
    # 1. Sign up the user
    signup_payload = {
        "email": user_data["email"],
        "password": user_data["password"],
        "data": {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"]
        }
    }
    signup_response = await async_client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code == status.HTTP_201_CREATED, f"Signup failed: {signup_response.text}"
    
    # 2. Log in the user
    login_payload = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    login_response = await async_client.post("/auth/login", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK, f"Login failed: {login_response.text}"
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # 3. Create a new client instance with the auth header
    #    We create a new one to avoid modifying the original async_client fixture state
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    async with AsyncClient(app=app, base_url="http://test", headers=auth_headers) as authed_client:
        yield authed_client
    
    # Optional: Add cleanup logic here if needed (e.g., delete the user from Supabase)
    # This requires implementing a way to interact with Supabase directly or via an API endpoint. 