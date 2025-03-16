import google.generativeai as genai
from fastapi.testclient import TestClient
from app import app
import sqlite3
import os

# Set your API key directly
genai.configure(api_key="AIzaSyC2i3QlrRobzcf3y2WHjTsCoaJe2cAqJB0")

# Function to chat with AI
def chat_with_ai(user_message):
    model = genai.GenerativeModel("gemini-1.5-pro")  # Free version
    response = model.generate_content(user_message)
    return response.text

# Test AI
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    response = chat_with_ai(user_input)
    print("AI:", response)

# Create a test client
client = TestClient(app)

# Test the home route
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Reminder Assistant" in response.text

# Test the chat endpoint with a general message
def test_chat_general():
    response = client.post(
        "/chat",
        json={"message": "Hello, how are you?"}
    )
    assert response.status_code == 200
    assert "reply" in response.json()

# Test the chat endpoint with a reminder request
def test_chat_reminder():
    response = client.post(
        "/chat",
        json={"message": "Remind me to call mom on April 15"}
    )
    assert response.status_code == 200
    assert "reply" in response.json()
    assert "Reminder" in response.json()["reply"]

# Test the chat endpoint with a show reminders request
def test_chat_show_reminders():
    response = client.post(
        "/chat",
        json={"message": "show reminders"}
    )
    assert response.status_code == 200
    assert "reply" in response.json()

# Test the direct reminder endpoint
def test_create_reminder():
    response = client.post(
        "/reminder",
        json={"message": "Buy groceries", "date": "2023-12-25"}
    )
    assert response.status_code == 200
    assert "message" in response.json()

# Test the get reminders endpoint
def test_get_reminders():
    response = client.get("/reminders")
    assert response.status_code == 200
    assert "reminders" in response.json()

# Run the tests
if __name__ == "__main__":
    # Setup test database
    if os.path.exists("reminders.db"):
        # Add a test reminder
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (user_message, date) VALUES (?, ?)", 
                      ("Test reminder", "2023-12-31"))
        conn.commit()
        conn.close()
    
    # Run tests
    test_read_main()
    test_chat_general()
    test_chat_reminder()
    test_chat_show_reminders()
    test_create_reminder()
    test_get_reminders()
    
    print("All tests passed!")
