from pydantic import BaseModel, EmailStr
from fastapi import Form # Import Form

# Schema for user registration input
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Schema for user login input
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    # Add class method to parse as form data
    @classmethod
    def as_form(cls,
                email: str = Form(...),
                password: str = Form(...)):
        return cls(email=email, password=password)

# Schema for the token response after successful login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" 