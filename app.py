"""
Advanced Reminder AI Assistant - Main Entry Point

This file serves as a compatibility layer for the old app.py structure.
It imports and uses the new modular structure from the app package.
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
