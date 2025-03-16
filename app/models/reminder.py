from pydantic import BaseModel, Field
from typing import List, Optional

class ReminderRequest(BaseModel):
    """Request model for creating a reminder"""
    message: str
    date: str
    priority: Optional[str] = "normal"
    tags: Optional[List[str]] = []

class ReminderResponse(BaseModel):
    """Response model for reminder data"""
    id: int
    message: str
    date: str
    priority: str
    tags: List[str]
    completed: bool = False 