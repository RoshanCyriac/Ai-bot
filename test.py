import google.generativeai as genai

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
