from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from pydantic import BaseModel, Field
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime, timedelta
import re
import json
import logging
import uuid
from typing import List, Optional, Dict, Any
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("reminder-ai")

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Reminder AI Assistant",
    description="A sophisticated FastAPI application that uses Google's Gemini AI with tools to manage reminders and tasks",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup template directory
templates = Jinja2Templates(directory="templates")

# Set up Google Gemini AI
# Replace with your actual API key or use environment variables
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC2i3QlrRobzcf3y2WHjTsCoaJe2cAqJB0")
genai.configure(api_key=API_KEY)

# Database setup
DB_FILE = "reminders.db"

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ReminderRequest(BaseModel):
    message: str
    date: str
    priority: Optional[str] = "normal"
    tags: Optional[List[str]] = []

class ReminderResponse(BaseModel):
    id: int
    message: str
    date: str
    priority: str
    tags: List[str]
    created_at: str

class ConversationHistory(BaseModel):
    id: str
    messages: List[Dict[str, Any]]

# Database functions
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create reminders table with additional fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                date TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                tags TEXT DEFAULT '[]',
                completed BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create conversation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                messages TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# Initialize database
init_db()

# Helper functions
def parse_date(date_string):
    """Convert various date formats to a standard format"""
    try:
        # Handle relative dates
        lower_date = date_string.lower()
        today = datetime.now()
        
        if "today" in lower_date:
            return today.strftime("%Y-%m-%d")
        elif "tomorrow" in lower_date:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in lower_date:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Try to parse month names
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        for month_name, month_num in months.items():
            if month_name in lower_date:
                # Try to extract day
                day_match = re.search(r'\d+', lower_date)
                if day_match:
                    day = int(day_match.group())
                    year = today.year
                    # If the month is earlier than current and day has passed, assume next year
                    if month_num < today.month or (month_num == today.month and day < today.day):
                        year += 1
                    return f"{year}-{month_num:02d}-{day:02d}"
        
        # If all else fails, return the original string
        return date_string
    except Exception as e:
        logger.error(f"Error parsing date: {str(e)}")
        return date_string

def format_reminder(reminder):
    """Format a reminder row as a dictionary"""
    try:
        tags = json.loads(reminder["tags"])
    except:
        tags = []
    
    return {
        "id": reminder["id"],
        "message": reminder["user_message"],
        "date": reminder["date"],
        "priority": reminder["priority"],
        "tags": tags,
        "completed": bool(reminder["completed"])
    }

# Core functionality
async def add_reminder(message, date, priority="normal", tags=None):
    """Add a reminder to the database"""
    try:
        if tags is None:
            tags = []
        
        # Parse the date to a standard format
        parsed_date = parse_date(date)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_message, date, priority, tags) VALUES (?, ?, ?, ?)",
            (message, parsed_date, priority, json.dumps(tags))
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        
        # Fetch the inserted reminder
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        conn.close()
        
        formatted_reminder = format_reminder(reminder)
        return {
            "success": True,
            "message": f"✅ Reminder added: {message} on {parsed_date}",
            "reminder": formatted_reminder
        }
    except Exception as e:
        logger.error(f"Error adding reminder: {str(e)}")
        return {
            "success": False,
            "message": f"Error adding reminder: {str(e)}"
        }

async def get_reminders(date_filter=None, completed=False):
    """Get reminders from the database with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM reminders WHERE completed = ?"
        params = [1 if completed else 0]
        
        if date_filter:
            query += " AND date = ?"
            params.append(date_filter)
        
        query += " ORDER BY date ASC, priority DESC"
        
        cursor.execute(query, params)
        reminders = cursor.fetchall()
        conn.close()
        
        if not reminders:
            return {
                "success": True,
                "message": "No reminders found" + (f" for {date_filter}" if date_filter else ""),
                "reminders": []
            }
        
        formatted_reminders = [format_reminder(r) for r in reminders]
        
        result_message = "📅 Here are your reminders:\n"
        for r in formatted_reminders:
            priority_icon = "🔴" if r["priority"] == "high" else "🟡" if r["priority"] == "medium" else "🟢"
            result_message += f"{priority_icon} {r['date']}: {r['message']}\n"
        
        return {
            "success": True,
            "message": result_message,
            "reminders": formatted_reminders
        }
    except Exception as e:
        logger.error(f"Error retrieving reminders: {str(e)}")
        return {
            "success": False,
            "message": f"Error retrieving reminders: {str(e)}",
            "reminders": []
        }

async def complete_reminder(reminder_id):
    """Mark a reminder as completed"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if reminder exists
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            conn.close()
            return {
                "success": False,
                "message": f"Reminder with ID {reminder_id} not found"
            }
        
        # Mark as completed
        cursor.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"✅ Reminder '{reminder['user_message']}' marked as completed"
        }
    except Exception as e:
        logger.error(f"Error completing reminder: {str(e)}")
        return {
            "success": False,
            "message": f"Error completing reminder: {str(e)}"
        }

async def delete_reminder(reminder_id):
    """Delete a reminder from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if reminder exists
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            conn.close()
            return {
                "success": False,
                "message": f"Reminder with ID {reminder_id} not found"
            }
        
        # Delete the reminder
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"🗑️ Reminder '{reminder['user_message']}' deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting reminder: {str(e)}")
        return {
            "success": False,
            "message": f"Error deleting reminder: {str(e)}"
        }

async def get_upcoming_reminders():
    """Get reminders for today and tomorrow"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM reminders WHERE date IN (?, ?) AND completed = 0 ORDER BY date ASC, priority DESC",
            (today, tomorrow)
        )
        reminders = cursor.fetchall()
        conn.close()
        
        if not reminders:
            return {
                "success": True,
                "message": "No upcoming reminders for today or tomorrow",
                "reminders": []
            }
        
        formatted_reminders = [format_reminder(r) for r in reminders]
        
        result_message = "⏰ Here are your upcoming reminders:\n"
        for r in formatted_reminders:
            day = "Today" if r["date"] == today else "Tomorrow"
            priority_icon = "🔴" if r["priority"] == "high" else "🟡" if r["priority"] == "medium" else "🟢"
            result_message += f"{priority_icon} {day}: {r['message']}\n"
        
        return {
            "success": True,
            "message": result_message,
            "reminders": formatted_reminders
        }
    except Exception as e:
        logger.error(f"Error retrieving upcoming reminders: {str(e)}")
        return {
            "success": False,
            "message": f"Error retrieving upcoming reminders: {str(e)}",
            "reminders": []
        }

# Conversation history functions
async def save_conversation(conversation_id, user_message, ai_response):
    """Save conversation history to the database"""
    try:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if conversation exists
        cursor.execute("SELECT messages FROM conversations WHERE id = ?", (conversation_id,))
        result = cursor.fetchone()
        
        if result:
            messages = json.loads(result["messages"])
        else:
            messages = []
        
        # Add new messages
        timestamp = datetime.now().isoformat()
        messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": timestamp
        })
        messages.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": timestamp
        })
        
        # Update or insert conversation
        if result:
            cursor.execute(
                "UPDATE conversations SET messages = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(messages), conversation_id)
            )
        else:
            cursor.execute(
                "INSERT INTO conversations (id, messages) VALUES (?, ?)",
                (conversation_id, json.dumps(messages))
            )
        
        conn.commit()
        conn.close()
        
        return conversation_id
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        return conversation_id

async def get_conversation_history(conversation_id):
    """Get conversation history from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT messages FROM conversations WHERE id = ?", (conversation_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result["messages"])
        return []
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        return []

# Gemini AI with tools
def create_gemini_tools():
    """Create tools definition for Gemini"""
    return [
        {
            "name": "add_reminder",
            "description": "Add a new reminder with a date, priority, and optional tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The reminder message content"
                    },
                    "date": {
                        "type": "string",
                        "description": "The date for the reminder (can be a specific date like '2023-12-25' or relative like 'tomorrow', 'next week', 'April 15')"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "medium", "high"],
                        "description": "The priority level of the reminder"
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional tags to categorize the reminder"
                    }
                },
                "required": ["message", "date"]
            }
        },
        {
            "name": "get_reminders",
            "description": "Get all reminders, optionally filtered by date",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optional date filter (e.g., 'today', 'tomorrow', '2023-12-25')"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Whether to show completed reminders (default: false)"
                    }
                }
            }
        },
        {
            "name": "complete_reminder",
            "description": "Mark a reminder as completed",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "The ID of the reminder to mark as completed"
                    }
                },
                "required": ["reminder_id"]
            }
        },
        {
            "name": "delete_reminder",
            "description": "Delete a reminder",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "The ID of the reminder to delete"
                    }
                },
                "required": ["reminder_id"]
            }
        },
        {
            "name": "get_upcoming_reminders",
            "description": "Get reminders for today and tomorrow",
            "parameters": {
                "type": "object",
                "properties": {
                    "dummy": {
                        "type": "string",
                        "description": "This parameter is not used but is required for the API"
                    }
                }
            }
        }
    ]

async def process_with_gemini(user_message, conversation_history=None):
    """Process user message with Gemini AI and tools"""
    try:
        # Initialize model with tools
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        
        # Prepare conversation context
        messages = []
        
        # Add system prompt
        system_prompt = """
        You are an advanced AI assistant that helps users manage their reminders and tasks.
        You can create reminders, list existing reminders, mark reminders as completed, and delete reminders.
        
        When a user wants to create a reminder, extract the task and date from their message.
        If they don't specify a date, ask for one.
        If they don't specify a priority, assume "normal".
        
        IMPORTANT: Always use the appropriate function call when the user wants to:
        - Create a reminder (use add_reminder)
        - List reminders (use get_reminders)
        - Complete a reminder (use complete_reminder)
        - Delete a reminder (use delete_reminder)
        - See upcoming reminders (use get_upcoming_reminders)
        
        Be helpful, concise, and friendly in your responses.
        """
        
        # Create the conversation
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})
        
        # Add current user message with system prompt
        messages = [
            {"role": "user", "parts": [f"{system_prompt}\n\nUser message: {user_message}"]}
        ]
        
        # Generate response with tools
        tools = create_gemini_tools()
        
        logger.info(f"Sending request to Gemini with tools: {json.dumps(tools)[:100]}...")
        
        function_call = None
        response_text = None
        
        # Try the first format (preferred)
        try:
            response = model.generate_content(
                messages,
                tools=tools,
                tool_config={"function_calling": "auto"}
            )
            
            # Check if the model wants to call a function
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            function_call = part.function_call
                            break
                        elif hasattr(part, 'text'):
                            response_text = part.text
            
            logger.info("Successfully processed with first format")
            
        except Exception as e1:
            logger.warning(f"First attempt failed: {str(e1)}")
            
            # Try the second format
            try:
                response = model.generate_content(
                    messages,
                    tools=[{"function_declarations": tools}]
                )
                
                # Check if the model wants to call a function
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_call = part.function_call
                                break
                            elif hasattr(part, 'text'):
                                response_text = part.text
                
                logger.info("Successfully processed with second format")
                
            except Exception as e2:
                logger.warning(f"Second attempt failed: {str(e2)}")
                
                # Fall back to no tools as a last resort
                try:
                    response = model.generate_content(messages)
                    
                    if hasattr(response, 'text'):
                        response_text = response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    response_text = part.text
                    
                    logger.info("Successfully processed without tools")
                    
                except Exception as e3:
                    logger.error(f"All attempts failed: {str(e3)}")
                    return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
        
        # If function call is requested
        if function_call:
            function_name = function_call.name
            
            # Fix for MapComposite object handling
            try:
                # First try direct JSON parsing
                function_args = json.loads(function_call.args)
            except (TypeError, json.JSONDecodeError):
                # If that fails, try handling MapComposite objects
                try:
                    # Initialize empty dict for arguments
                    function_args = {}
                    
                    # Check if it has _pb attribute (MapComposite structure)
                    if hasattr(function_call.args, '_pb'):
                        pb_dict = function_call.args._pb
                        
                        # Extract values from the nested structure
                        for key, value in pb_dict.items():
                            # Extract the actual string value from the protobuf structure
                            if hasattr(value, 'string_value') and value.string_value:
                                function_args[key] = value.string_value
                            elif hasattr(value, 'bool_value'):
                                function_args[key] = value.bool_value
                            elif hasattr(value, 'number_value'):
                                function_args[key] = value.number_value
                            elif hasattr(value, 'list_value') and hasattr(value.list_value, 'values'):
                                # Handle list values
                                function_args[key] = [
                                    v.string_value if hasattr(v, 'string_value') else v 
                                    for v in value.list_value.values
                                ]
                    # If no _pb attribute, try __dict__ or dict() conversion
                    elif hasattr(function_call.args, '__dict__'):
                        function_args = function_call.args.__dict__
                    else:
                        function_args = dict(function_call.args)
                        
                except Exception as e:
                    logger.error(f"Failed to extract function args from MapComposite: {str(e)}")
                    function_args = {}
            
            logger.info(f"Function call: {function_name} with args: {function_args}")
            
            # Execute the appropriate function
            if function_name == "add_reminder":
                result = await add_reminder(
                    function_args.get("message"),
                    function_args.get("date"),
                    function_args.get("priority", "normal"),
                    function_args.get("tags", [])
                )
            elif function_name == "get_reminders":
                result = await get_reminders(
                    function_args.get("date"),
                    function_args.get("completed", False)
                )
            elif function_name == "complete_reminder":
                result = await complete_reminder(function_args.get("reminder_id"))
            elif function_name == "delete_reminder":
                result = await delete_reminder(function_args.get("reminder_id"))
            elif function_name == "get_upcoming_reminders":
                result = await get_upcoming_reminders()
            else:
                result = {
                    "success": False,
                    "message": f"Unknown function: {function_name}"
                }
            
            # Return the function result
            return result.get("message")
        
        # If no function call was detected, return the model's response
        return response_text or "I'm sorry, I couldn't process your request. Please try rephrasing your message."
    
    except Exception as e:
        logger.error(f"Error processing with Gemini: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}"

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        user_message = data.get("message", "")
        conversation_id = data.get("conversation_id")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get conversation history if conversation_id is provided
        conversation_history = []
        if conversation_id:
            conversation_history = await get_conversation_history(conversation_id)
        
        # Process with Gemini
        response_text = await process_with_gemini(user_message, conversation_history)
        
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
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reminder")
async def create_reminder(reminder: ReminderRequest):
    try:
        result = await add_reminder(
            reminder.message,
            reminder.date,
            reminder.priority,
            reminder.tags
        )
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in create_reminder endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reminders")
async def list_reminders(
    date: Optional[str] = None,
    completed: bool = False
):
    try:
        result = await get_reminders(date, completed)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in list_reminders endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reminder/{reminder_id}/complete")
async def mark_complete(reminder_id: int):
    try:
        result = await complete_reminder(reminder_id)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in mark_complete endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/reminder/{reminder_id}")
async def remove_reminder(reminder_id: int):
    try:
        result = await delete_reminder(reminder_id)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in remove_reminder endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reminders/upcoming")
async def upcoming_reminders():
    try:
        result = await get_upcoming_reminders()
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in upcoming_reminders endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    try:
        messages = await get_conversation_history(conversation_id)
        return JSONResponse({
            "conversation_id": conversation_id,
            "messages": messages
        })
    except Exception as e:
        logger.error(f"Error in get_conversation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application with: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
