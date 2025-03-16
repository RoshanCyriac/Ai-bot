# AI Reminder Assistant

A FastAPI application that uses Google's Gemini AI to provide a chat interface with reminder functionality.

## Features

- Chat with Google's Gemini AI model
- Set reminders using natural language
- View all reminders
- Modern, responsive UI

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
pip install fastapi uvicorn google-generativeai jinja2 python-multipart
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
http://127.0.0.1:8000
```

## Usage

- **Chat with AI**: Type any message and press Enter or click Send
- **Set a Reminder**: Type a message containing "remind me" and a date (e.g., "Remind me to call mom on April 15")
- **View Reminders**: Type "show reminders" or click the "Show All Reminders" button

## API Endpoints

- `GET /`: Main web interface
- `POST /chat`: Send a message to the AI
- `POST /reminder`: Create a reminder directly
- `GET /reminders`: Get all reminders

## Testing

Run the tests with:
```bash
python test.py
```

## Project Structure

- `app.py`: Main FastAPI application
- `templates/`: HTML templates
- `static/`: CSS and JavaScript files
- `reminders.db`: SQLite database for storing reminders
- `test.py`: Test suite

## License

MIT

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Generative AI](https://ai.google.dev/) 