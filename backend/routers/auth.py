from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from supabase.lib.client_options import ClientOptions
from supabase.lib.errors import AuthApiError

from ..schemas.auth import UserCreate, UserLogin, Token # Import UserLogin and Token
from ..database import get_db_client # Import the db client dependency

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/signup") # Define the POST endpoint for signup
async def signup(user_data: UserCreate, db: Client = Depends(get_db_client)):
    try:
        # 1. Sign up the user using Supabase Auth
        auth_response = db.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        # Check if Supabase returned a user object (sign up might require confirmation)
        if auth_response.user is None:
            # If no user object, but no error, likely needs email confirmation
            # You might want to return a specific message here
            if auth_response.session is None and not auth_response.user:
                 return {"message": "Signup successful, please check your email for confirmation."}
            else:
                 # Handle unexpected cases if necessary
                 raise HTTPException(status_code=400, detail="Signup failed, unexpected response from auth provider.")

        supabase_user_id = auth_response.user.id

        # 2. Insert user details into our public.users table
        # You might want to set a default subscription tier here
        insert_response = db.table('users')\
                            .insert({
                                'user_id': str(supabase_user_id), 
                                'email': user_data.email,
                                'password_hash': '-', # Don't store password hash here, Supabase handles it
                                'subscription_tier': 'Free' # Example default tier
                            })\
                            .execute()

        # Check if insert failed
        if not insert_response.data:
            # Consider how to handle this - maybe delete the Supabase auth user?
            # For now, raise an error.
            raise HTTPException(status_code=500, detail="Failed to create user profile in database.")

        # Return a success message or user info (excluding sensitive data)
        # Supabase might require email confirmation, tailor message accordingly
        return {"message": "Signup successful!", "user_id": supabase_user_id, "email": user_data.email}

    except AuthApiError as e:
        # Handle specific Supabase Auth errors (e.g., user already registered)
        if "User already registered" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered.")
        # Handle other auth errors
        raise HTTPException(status_code=400, detail=f"Authentication error: {e}")
    except Exception as e:
        # Handle general errors (e.g., database connection issues)
        print(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during signup.")

# Add the login endpoint
@router.post("/login", response_model=Token) # Use Token as the response model
async def login(user_data: UserLogin, db: Client = Depends(get_db_client)):
    try:
        # Authenticate user with Supabase
        response = db.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })

        # Check if login was successful and session exists
        if response.session and response.session.access_token:
            return Token(access_token=response.session.access_token, token_type="bearer")
        else:
            # This case might indicate issues other than wrong password, like unconfirmed email
            # Supabase typically raises AuthApiError for wrong credentials
            raise HTTPException(status_code=401, detail="Login failed, please check your credentials or confirm your email.")

    except AuthApiError as e:
        # Specific error for invalid login credentials
        if "Invalid login credentials" in str(e):
             raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}, # Standard header for unauthorized bearer token
            )
        # Handle other potential auth errors during login
        raise HTTPException(status_code=400, detail=f"Authentication error: {e}")
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during login.") 