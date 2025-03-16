# AI Reminder Assistant with Function Calling

A FastAPI application that uses Google's Gemini AI with function calling capabilities to provide a chat interface with reminder functionality.

## Features

- Chat with Google's Gemini AI model
- Set reminders using natural language
- View all reminders
- Uses Gemini's function calling to intelligently handle reminder operations
- Modern, responsive UI

## How Function Calling Works

This application uses Gemini's function calling capabilities to:

1. Define tools (functions) that the AI can use
2. Let the AI decide when to call these functions based on user intent
3. Execute the appropriate function when the AI determines it's needed
4. Return the function's result to the user

This approach is more flexible than keyword matching because:
- The AI understands user intent more naturally
- Users can phrase their requests in many different ways
- The AI extracts the necessary parameters from natural language

## Requirements

- Python 3.8+
- FastAPI
- Google Generative AI Python SDK
- SQLite3
- Uvicorn (ASGI server)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ai-reminder-assistant
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up your Google Gemini API key:
   - Get an API key from [Google AI Studio](https://makersuite.google.com/)
   - Replace the placeholder API key in `app.py` with your actual key

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app:app --reload
```

2. Open your browser and navigate to:
```