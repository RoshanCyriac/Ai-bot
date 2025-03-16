# Advanced AI Reminder Assistant

A powerful AI assistant that helps you manage reminders and now supports general chat functionality.

## Features

### Reminder Management
- Create reminders with natural language
- Set dates, priorities, and tags
- View, complete, and delete reminders
- Filter reminders by date and completion status

### General Chat
- Toggle between reminder mode and general chat mode
- Ask questions on any topic in general chat mode
- Get informative responses powered by Google's Gemini AI
- Maintain separate conversation histories for each mode

## How to Use

1. **Reminder Mode (Default)**
   - Create reminders: "Remind me to call mom tomorrow"
   - List reminders: "Show me all my reminders"
   - Complete reminders: "Mark reminder #3 as done"
   - Delete reminders: "Delete reminder #2"

2. **General Chat Mode**
   - Toggle to general chat mode using the switch in the header
   - Ask any question: "What's the capital of France?"
   - Have casual conversations: "Tell me a joke"
   - Get information: "How does photosynthesis work?"

## Technical Details

The application uses:
- FastAPI for the backend
- Google's Gemini AI for natural language processing
- SQLite for data storage
- Function calling for structured reminder operations
- Separate endpoints for reminder and general chat functionality

## Setup and Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file in the root directory with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key
   ```
4. Run the application: `python app.py`
5. Access the web interface at `http://localhost:8000`

## License

MIT License