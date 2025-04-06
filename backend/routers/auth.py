from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from supabase.lib.client_options import ClientOptions
from gotrue.errors import AuthApiError

from ..schemas.auth import UserCreate, UserLogin, Token # Import UserLogin and Token
from ..dependencies import get_supabase_client # Use corrected import path

router = APIRouter(
    prefix="/api/auth", # Add /api prefix
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/signup", status_code=201) # Define the POST endpoint for signup, set success code
async def signup(user_data: UserCreate, db: Client = Depends(get_supabase_client)):
    """Handles new user registration."""
    try:
        # 1. Sign up the user using Supabase Auth
        auth_response = db.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            # Include optional data if your Supabase setup requires it
            # "options": {
            #     "data": user_data.data.dict() if user_data.data else {}
            # }
        })
        
        # Check if Supabase returned a user object (sign up might require confirmation)
        if auth_response.user is None:
            # If no user object, but no error, likely needs email confirmation
            if auth_response.session is None:
                 return {"message": "Signup successful, please check your email for confirmation."}
            else:
                 # Handle unexpected cases if necessary
                 raise HTTPException(status_code=400, detail="Signup failed, unexpected response from auth provider.")

        supabase_user_id = auth_response.user.id

        # 2. Insert minimal user details into our public.users table
        # Keep this minimal, primary user data is in Supabase Auth
        # Remove Supabase table insertion as it might fail due to permission errors
        # Consider a separate function/trigger if profile data is needed
        # insert_response = db.table('users')\
        #                     .insert({
        #                         'user_id': str(supabase_user_id),
        #                         'email': user_data.email,
        #                     })\
        #                     .execute()

        # # Check if insert failed
        # if hasattr(insert_response, 'error') and insert_response.error:
        #     print(f"Database insert error for user {supabase_user_id}: {insert_response.error}")
        #     raise HTTPException(status_code=500, detail="Failed to create user profile in database.")

        # Return success message (adjusted for potentially pending confirmation)
        return {
            "message": "Signup initiated successfully! Please check your email for confirmation if required.",
            "user": {
                "id": supabase_user_id,
                "email": user_data.email
            }
        }

    except AuthApiError as e:
        # Handle specific Supabase Auth errors (e.g., user already registered)
        if "User already registered" in str(e) or (e.status == 400 and "user already exists" in e.message.lower()):
            raise HTTPException(status_code=409, detail="Email already registered.") # 409 Conflict is more specific
        elif "weak password" in str(e).lower():
             raise HTTPException(status_code=400, detail=f"Password is too weak: {e}")
        # Handle other auth errors
        raise HTTPException(status_code=400, detail=f"Authentication error: {e}")
    except Exception as e:
        # Handle general errors (e.g., database connection issues)
        print(f"Error during signup: {e}") # Log the error
        raise HTTPException(status_code=500, detail="An internal server error occurred during signup.")

# Add the login endpoint
@router.post("/login", response_model=Token) # Use Token as the response model
async def login(
    # Use the UserLogin.as_form method for dependency injection
    form_data: UserLogin = Depends(UserLogin.as_form),
    db: Client = Depends(get_supabase_client)
    ):
    """Handles user login and returns an access token."""
    try:
        # Authenticate user with Supabase using email/password
        response = db.auth.sign_in_with_password({
            "email": form_data.email,
            "password": form_data.password
        })

        # Check if login was successful and session exists
        if response.session and response.session.access_token:
            return Token(access_token=response.session.access_token, token_type="bearer")
        else:
            # This case might indicate issues other than wrong password, like unconfirmed email
            # Supabase typically raises AuthApiError for wrong credentials
            raise HTTPException(
                status_code=401,
                detail="Login failed. Check credentials or confirm email.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except AuthApiError as e:
        # Specific error for invalid login credentials
        if "Invalid login credentials" in str(e) or (e.status == 400 and "invalid login credentials" in e.message.lower()):
             raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}, # Standard header for unauthorized bearer token
            )
        # Handle other potential auth errors during login (e.g., email not confirmed if required)
        print(f"AuthApiError during login for {form_data.email}: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {e.message}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        print(f"Error during login for {form_data.email}: {e}") # Log the error
        raise HTTPException(status_code=500, detail="An internal server error occurred during login.") 