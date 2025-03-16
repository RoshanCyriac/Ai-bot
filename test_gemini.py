import google.generativeai as genai
import json

# Set up the API key
API_KEY = "AIzaSyC2i3QlrRobzcf3y2WHjTsCoaJe2cAqJB0"  # This is the default key from client.py
genai.configure(api_key=API_KEY)

# Define tools
tools = [
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
                    "description": "The date for the reminder"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "medium", "high"],
                    "description": "The priority level of the reminder"
                }
            },
            "required": ["message", "date"]
        }
    }
]

# System prompt
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

# User message
user_message = "Remind me to call mom tomorrow"

# Create the conversation
messages = [
    {"role": "user", "parts": [f"{system_prompt}\n\nUser message: {user_message}"]}
]

try:
    # Initialize model
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
    )
    
    # Try with tools
    print("Attempting to call Gemini with tools...")
    response = model.generate_content(
        messages,
        tools=tools,
        tool_config={"function_calling": "auto"}
    )
    
    print("Response received!")
    print("Response type:", type(response))
    print("Response attributes:", dir(response))
    
    # Check for function call
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'content') and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, 'function_call'):
                    print("Function call detected!")
                    print("Function name:", part.function_call.name)
                    print("Function args:", part.function_call.args)
                elif hasattr(part, 'text'):
                    print("Text response:", part.text)
    
except Exception as e:
    print(f"Error: {str(e)}")
    
    # Try without tools as fallback
    try:
        print("\nFalling back to no tools...")
        response = model.generate_content(messages)
        
        if hasattr(response, 'text'):
            print("Text response:", response.text)
        else:
            print("No text response found")
            
    except Exception as e2:
        print(f"Fallback error: {str(e2)}") 