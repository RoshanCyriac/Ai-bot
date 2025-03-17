from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.requests import Request
from typing import Optional
import uuid

from app.models import ReminderRequest
from app.services import (
    add_reminder,
    get_reminders,
    complete_reminder,
    delete_reminder,
    get_upcoming_reminders,
    save_conversation,
    get_conversation_history
)
from app.gemini import process_with_gemini, process_general_chat

# Create router
router = APIRouter()

@router.post("/chat")
async def chat(request: Request, background_tasks: BackgroundTasks):
    """Process a chat message with Gemini AI - handles both reminder and general chat"""
    try:
        data = await request.json()
        user_message = data.get("message", "")
        conversation_id = data.get("conversation_id")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Generate a new conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Get conversation history if conversation_id is provided
        conversation_history = []
        if conversation_id:
            conversation_history = await get_conversation_history(conversation_id)
        
        # Determine if this is a reminder-related message or general chat
        is_reminder_related = any(keyword in user_message.lower() for keyword in 
                                ["remind", "reminder", "schedule", "task", "todo", "to-do", 
                                 "show reminders", "list reminders", "upcoming", "delete reminder", 
                                 "complete reminder", "mark as done", "mark as completed"])
        
        # Process with appropriate Gemini function
        if is_reminder_related:
            response_text = await process_with_gemini(user_message, conversation_history)
        else:
            response_text = await process_general_chat(user_message, conversation_history)
        
        # Save conversation in background
        background_tasks.add_task(
            save_conversation,
            conversation_id,
            user_message,
            response_text
        )
        
        return JSONResponse({
            "reply": response_text,
            "conversation_id": conversation_id
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keep the separate endpoints for backward compatibility but route them to the main chat endpoint
@router.post("/general-chat")
async def general_chat(request: Request, background_tasks: BackgroundTasks):
    """Process a general chat message with Gemini AI (redirects to main chat endpoint)"""
    return await chat(request, background_tasks)

@router.post("/reminder")
async def create_reminder(reminder: ReminderRequest):
    """Create a new reminder"""
    try:
        result = await add_reminder(
            reminder.message,
            reminder.date,
            reminder.priority,
            reminder.tags
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminders")
async def list_reminders(
    date: Optional[str] = None,
    completed: bool = False
):
    """Get all reminders with optional filtering"""
    try:
        result = await get_reminders(date, completed)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminder/{reminder_id}/complete")
async def mark_complete(reminder_id: int):
    """Mark a reminder as completed"""
    try:
        result = await complete_reminder(reminder_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reminder/{reminder_id}")
async def remove_reminder(reminder_id: int):
    """Delete a reminder"""
    try:
        result = await delete_reminder(reminder_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminders/upcoming")
async def upcoming_reminders():
    """Get upcoming reminders for today and tomorrow"""
    try:
        result = await get_upcoming_reminders()
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        messages = await get_conversation_history(conversation_id)
        return JSONResponse({
            "conversation_id": conversation_id,
            "messages": messages
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 