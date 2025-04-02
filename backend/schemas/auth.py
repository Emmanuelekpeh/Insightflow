from pydantic import BaseModel, EmailStr

# Schema for user registration input
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Schema for user login input
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Schema for the token response after successful login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" 