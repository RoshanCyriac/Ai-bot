from flask import Flask, render_template, request, jsonify
from datetime import datetime
import google.generativeai as genai
import sqlite3


# Configure API Key
genai.configure(api_key="AIzaSyC2i3QlrRobzcf3y2WHjTsCoaJe2cAqJB0")

# Choose a Gemini Model
model = genai.GenerativeModel("gemini-1.5-flash")  # Use a valid model

app = Flask(__name__)
def init_db():
    conn = sqlite3.connect("reminders.db")
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

init_db()  # Run this once to create the database
# Home Route
@app.route('/')
def index():
    return render_template("index.html")

# # AI Chat Route
# @app.route('/chat', methods=['POST'])
# def chat():
#     user_input = request.json['message']
    
#     try:
#         response = model.generate_content(user_input)
#         ai_response = response.text
#     except Exception as e:
#         ai_response = "Error: " + str(e)

#     return jsonify({'response': ai_response})
def add_reminder(user_message):
    # Extract date (for now, assume user enters a date like 'April 1st')
    date = extract_date_from_message(user_message)
    if not date:
        return "Please include a valid date in your reminder."

    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (user_message, date) VALUES (?, ?)", (user_message, date))
    conn.commit()
    conn.close()
    
    return f"Reminder set for {date}!"

def extract_date_from_message(message):
    # Simple example: Look for a date pattern (this can be improved with NLP)
    words = message.split()
    for word in words:
        if word.lower() in ["january", "february", "march", "april", "may", "june", 
                            "july", "august", "september", "october", "november", "december"]:
            return " ".join(words[-2:])  # Assume last 2 words are date
    return None
def get_reminders():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, date FROM reminders ORDER BY date ASC")
    reminders = cursor.fetchall()
    conn.close()
    
    if not reminders:
        return "No reminders found."
    
    return "\n".join([f"{reminder[1]}: {reminder[0]}" for reminder in reminders])
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"error": "No message received!"}), 400

    # Check if user wants to set a reminder
    if "remind me" in user_message.lower():
        response_text = add_reminder(user_message)
    elif "show reminders" in user_message.lower():
        response_text = get_reminders()
    else:
        response = model.generate_content(user_message)
        response_text = response.text

    return jsonify({"reply": response_text})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
