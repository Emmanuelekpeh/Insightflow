import pytest
from httpx import AsyncClient
from fastapi import status
import uuid # To generate unique emails for testing

# Import the FastAPI app instance
from backend.main import app
# Import helper from conftest
from backend.tests.conftest import generate_test_user 

# Reuse the client fixture from test_main.py (pytest finds it automatically)
# If test_main.py is not in the same directory or discoverable, you might need to import it
# or define the fixture again here.

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio

# --- Test Data ---
# Removed generate_test_user - now imported from conftest.py

# --- Test Cases ---

async def test_signup_success(async_client: AsyncClient):
    """Test successful user signup."""
    user_data = generate_test_user()
    payload = {
        "email": user_data["email"],
        "password": user_data["password"],
        "data": {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"]
        }
    }
    response = await async_client.post("/auth/signup", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["email"] == user_data["email"]
    assert "id" in response_data
    # IMPORTANT: Realistically, you'd want to clean up this user from Supabase
    # either here, in a fixture, or manually after testing.

async def test_signup_existing_email(async_client: AsyncClient):
    """Test signup attempt with an email that already exists."""
    user_data = generate_test_user()
    payload = {
        "email": user_data["email"],
        "password": user_data["password"],
        "data": {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"]
        }
    }
    
    # First signup (should succeed)
    response1 = await async_client.post("/auth/signup", json=payload)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Second signup attempt with the same email (should fail)
    response2 = await async_client.post("/auth/signup", json=payload)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST 
    # Check the detail message (might vary slightly based on Supabase response)
    assert "User already registered" in response2.json().get("detail", "")

async def test_login_success(async_client: AsyncClient):
    """Test successful user login after signing up."""
    user_data = generate_test_user()
    signup_payload = {
        "email": user_data["email"],
        "password": user_data["password"],
        "data": {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"]
        }
    }
    
    # Ensure user exists
    signup_response = await async_client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code == status.HTTP_201_CREATED
    
    # Attempt login
    login_payload = {
        "username": user_data["email"], # FastAPI's OAuth2PasswordRequestForm uses 'username'
        "password": user_data["password"]
    }
    # Note: Login expects form data, not JSON
    response = await async_client.post("/auth/login", data=login_payload)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"

async def test_login_incorrect_password(async_client: AsyncClient):
    """Test login attempt with an incorrect password."""
    user_data = generate_test_user()
    signup_payload = {
        "email": user_data["email"],
        "password": user_data["password"],
        "data": {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"]
        }
    }
    
    # Ensure user exists
    signup_response = await async_client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code == status.HTTP_201_CREATED

    # Attempt login with wrong password
    login_payload = {
        "username": user_data["email"],
        "password": "wrongPassword"
    }
    response = await async_client.post("/auth/login", data=login_payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json().get("detail", "")

async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login attempt with an email that does not exist."""
    login_payload = {
        "username": f"nonexistent_{uuid.uuid4()}@example.com",
        "password": "anyPassword"
    }
    response = await async_client.post("/auth/login", data=login_payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json().get("detail", "") 