from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
import os
import contextlib # For lifespan manager
import redis.asyncio as redis # For Arq pool
import arq # For Arq pool creation

# Load environment variables from .env file
load_dotenv()

# Fix imports to be absolute instead of relative
from backend.routers import dashboard, auth, newsletter

# --- Arq Redis Pool Management ---
# Reuse Redis settings (consider moving to a central config file later)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# --- CSP Middleware ---
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Define CSP policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' blob: data:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "connect-src 'self' https://api.mailersend.com; "
            "upgrade-insecure-requests;"
        )
        
        # Add CSP header
        response.headers["Content-Security-Policy"] = csp_policy
        return response

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create Arq Redis pool
    print("INFO:     Creating Arq Redis pool...")
    # TODO: Check if arq.connections.RedisSettings can take redis_url directly
    redis_settings = arq.connections.RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    arq_pool = await arq.create_pool(redis_settings)
    app.state.arq_pool = arq_pool # Store the pool in app state
    print("INFO:     Arq Redis pool created.")
    yield
    # Shutdown: Close Arq Redis pool
    print("INFO:     Closing Arq Redis pool...")
    if app.state.arq_pool:
        await app.state.arq_pool.close()
    print("INFO:     Arq Redis pool closed.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="InsightFlow API",
    description="API for market research insights, trends, and competitor analysis.",
    version="0.1.0",
    lifespan=lifespan # Add the lifespan manager
)

# --- CORS Middleware Configuration ---
# Define allowed origins. Replace placeholders with your actual frontend URLs.
# Use environment variables for production origins for flexibility.
FRONTEND_DEV_URL = os.getenv("FRONTEND_DEV_URL", "http://localhost:3000")
FRONTEND_PROD_URL = os.getenv("FRONTEND_PROD_URL", "https://YOUR_FRONTEND_RENDER_URL.onrender.com") # Placeholder

origins = [
    FRONTEND_DEV_URL,
    FRONTEND_PROD_URL,
    # Add any other origins if necessary (e.g., staging environment)
]

# Add CSP Middleware
app.add_middleware(CSPMiddleware)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Allow cookies
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# Add Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.onrender.com"  # Allow Render subdomains
    ]
)

@app.get("/", tags=["Health"])
async def read_root():
    """Root endpoint providing a simple hello message."""
    return {"message": "Welcome to InsightFlow API"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Include routers
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(newsletter.router)

# Placeholder for future routers
# from routers import users, trends, competitors, etc.
# app.include_router(users.router)
# app.include_router(trends.router)
# app.include_router(competitors.router)

if __name__ == "__main__":
    import uvicorn
    # Note: Uvicorn reload might interfere with lifespan state in some cases.
    # For production, run without reload.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)