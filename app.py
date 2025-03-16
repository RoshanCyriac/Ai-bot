from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import re

# Initialize FastAPI app
app = FastAPI(title="Reminder AI Assistant", 
              description="A FastAPI application that uses Google's Gemini AI to chat and manage reminders")

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup template directory
templates = Jinja2Templates(directory="templates")

# Set up Google Gemini AI
# Replace with your actual API key or use environment variables
API_KEY = "AIzaSyC2i3QlrRobzcf3y2WHjTsCoaJe2cAqJB0"  # Replace with your actual key
os.environ["GOOGLE_API_KEY"] = API_KEY
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Database setup
DB_FILE = "reminders.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Pydantic models for request validation
class ChatRequest(BaseModel):
    message: str

class ReminderRequest(BaseModel):
    message: str
    date: str  # Example format: "2025-04-10"

# Extract date from message using regex
def extract_date_from_message(message):
    # Look for month names
    months = ["january", "february", "march", "april", "may", "june", 
              "july", "august", "september", "october", "november", "december"]
    
    words = message.lower().split()
    for i, word in enumerate(words):
        if word in months and i < len(words) - 1:
            # Try to extract a date like "April 15" or "April 15th"
            try:
                month = word.capitalize()
                day = re.sub(r'[^0-9]', '', words[i+1])  # Remove non-numeric characters
                if day:
                    return f"{month} {day}"
            except:
                pass
    
    # If no date found, return None
    return None

# AI Chat Function
def chat_with_ai(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text.strip()
    except Exception as e:
        print(f"Error with AI model: {str(e)}")
        return "Sorry, I'm having trouble connecting to the AI service right now."

# Add Reminder Function
def add_reminder(user_message, date=None):
    # If date is not provided, try to extract it from the message
    if not date:
        date = extract_date_from_message(user_message)
        if not date:
            return "I couldn't find a date in your message. Please specify when you want to be reminded."
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (user_message, date) VALUES (?, ?)", (user_message, date))
    conn.commit()
    conn.close()
    return f"Reminder added: {user_message} on {date}"

# Get Reminders Function
def get_all_reminders():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders ORDER BY date ASC")
    reminders = cursor.fetchall()
    conn.close()
    
    if not reminders:
        return "You don't have any reminders set."
    
    result = "Here are your reminders:\n"
    for r in reminders:
        result += f"- {r[2]}: {r[1]}\n"
    
    return result

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Check if the message is about reminders
        if "remind me" in user_message.lower():
            response_text = add_reminder(user_message)
        elif "show reminders" in user_message.lower() or "get reminders" in user_message.lower():
            response_text = get_all_reminders()
        else:
            # Use AI for general conversation
            response_text = chat_with_ai(user_message)
        
        return {"reply": response_text}
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reminder")
async def create_reminder(reminder: ReminderRequest):
    try:
        result = add_reminder(reminder.message, reminder.date)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reminders")
async def get_reminders():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reminders ORDER BY date ASC")
        reminders = cursor.fetchall()
        conn.close()
        
        return {"reminders": [{"id": r[0], "message": r[1], "date": r[2]} for r in reminders]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the application with: uvicorn app:app --reload
