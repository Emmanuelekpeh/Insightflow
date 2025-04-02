from fastapi import FastAPI
from dotenv import load_dotenv
import os
import contextlib # For lifespan manager
import redis.asyncio as redis # For Arq pool
import arq # For Arq pool creation

# Load environment variables from .env file
load_dotenv()

# Fix imports to be absolute instead of relative
from backend.routers import dashboard, auth

# --- Arq Redis Pool Management ---
# Reuse Redis settings (consider moving to a central config file later)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create Arq Redis pool
    print("INFO:     Creating Arq Redis pool...")
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