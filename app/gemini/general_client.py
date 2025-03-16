import json
import logging
import os
from typing import Dict, Any, List, Optional

import google.generativeai as genai

# Configure logger
logger = logging.getLogger("reminder-ai.gemini.general")

# Set up Google Gemini AI (reusing the same API key)
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC2i3QlrRobzcf3y2WHjTsCoaJe2cAqJB0")
genai.configure(api_key=API_KEY)

# System prompt for general chat
GENERAL_SYSTEM_PROMPT = """
You are an advanced AI assistant that can help with a wide range of topics.
You can provide information, answer questions, have casual conversations, and assist with various tasks.

You should be:
- Helpful and informative: Provide accurate, factual information and useful responses
- Conversational and engaging: Maintain a natural, friendly tone
- Concise: Keep responses clear and to the point
- Respectful: Be polite and considerate in all interactions

If the user asks about reminders or tasks, suggest they use the reminder-specific features of the application.
"""

async def process_general_chat(user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Process user message with Gemini AI for general chat
    
    Args:
        user_message: The user's message
        conversation_history: Optional conversation history
        
    Returns:
        The AI's response
    """
    try:
        # Initialize model without tools for general chat
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
        
        # Create the conversation
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})
        
        # Add current user message with system prompt
        messages = [
            {"role": "user", "parts": [f"{GENERAL_SYSTEM_PROMPT}\n\nUser message: {user_message}"]}
        ]
        
        logger.info("Sending general chat request to Gemini...")
        
        # Generate response without tools
        try:
            response = model.generate_content(messages)
            
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            response_text = part.text
            
            logger.info("Successfully processed general chat")
            
            return response_text or "I'm sorry, I couldn't process your request. Please try again."
            
        except Exception as e:
            logger.error(f"Error in general chat: {str(e)}")
            return f"I'm sorry, I encountered an error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error processing with Gemini: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}" 