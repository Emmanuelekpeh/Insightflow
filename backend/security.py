from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from gotrue.errors import AuthApiError
from supabase import Client, create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Supabase Client Initialization ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Optional: For admin actions

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
# Optional: Initialize admin client if service key is provided
supabase_admin_client: Optional[Client] = None
if SUPABASE_SERVICE_KEY:
    try:
        supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Supabase admin client initialized.")
    except Exception as e:
        print(f"Warning: Could not initialize Supabase admin client: {e}")

# --- Dependency Functions ---
def get_supabase_client() -> Client:
    """Dependency to get the Supabase anonymous client."""
    return supabase_client

def get_supabase_admin_client() -> Optional[Client]:
    """Dependency to get the Supabase admin client (if available)."""
    if not supabase_admin_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase admin service key not configured"
        )
    return supabase_admin_client

# HTTP Bearer scheme for token extraction
bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Client = Depends(get_supabase_client)):
    """Validate JWT token and return the authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        # Verify the JWT token with Supabase
        user_response = db.auth.get_user(token)
        if user_response.user:
            return user_response.user
        else:
            # This case might occur if the token is valid but user info couldn't be fetched
            # Or if the response format changes
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except AuthApiError as e:
        # Handle specific errors like expired token, invalid token, etc.
        print(f"AuthApiError validating token: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e.message}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"Unexpected error during token validation: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error.",
        )

# Removed the old get_supabase_client() function as it's replaced by the dependency. 