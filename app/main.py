from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_all_tables
from app.routers import auth_router, users_router
from app.utils.logging import get_logger

# Setup logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Barbershop User Service",
    description="User management microservice for the barbershop appointment system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(users_router, prefix="/api/users")


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Barbershop User Service")
    create_all_tables()
    logger.info("Database tables created")


# Health check endpoint (Hello world)
@app.get("/", tags=["health"])
async def health_check():
    logger.debug("Health check endpoint called")
    return {
        "status": "healthy",
        "service": "barbershop-user-service",
        "version": app.version,
    }


# Main entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
