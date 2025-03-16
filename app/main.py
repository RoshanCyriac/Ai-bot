import logging
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse
import re

from app import __version__
from app.api import api_router, frontend_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("reminder-ai")

# Define API compatibility middleware
class APICompatibilityMiddleware(BaseHTTPMiddleware):
    """Middleware to redirect old API paths to new ones"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Define patterns for old API paths
        api_patterns = [
            r"^/reminders(/upcoming)?$",
            r"^/reminder(/\d+(/complete)?)?$",
            r"^/chat$",
            r"^/conversations/[^/]+$"
        ]
        
        # Check if the path matches any of the old API patterns
        if any(re.match(pattern, path) for pattern in api_patterns):
            # Skip if already accessing the new API path
            if not path.startswith("/api"):
                new_path = f"/api{path}"
                logger.info(f"Redirecting old path {path} to {new_path}")
                
                # Use 307 for POST/DELETE to preserve the method and body
                if request.method in ["POST", "DELETE", "PUT", "PATCH"]:
                    return RedirectResponse(new_path, status_code=307)
                else:
                    return RedirectResponse(new_path)
        
        # Continue with the regular request
        return await call_next(request)

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Reminder AI Assistant",
    description="A sophisticated FastAPI application that uses Google's Gemini AI with tools to manage reminders and tasks",
    version=__version__
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API compatibility middleware
app.add_middleware(APICompatibilityMiddleware)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(frontend_router)
app.include_router(api_router, prefix="/api")

# Run the application with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 