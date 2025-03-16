from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str
    conversation_id: Optional[str] = None

class ConversationHistory(BaseModel):
    """Model for conversation history"""
    id: str
    messages: List[Dict[str, Any]] 