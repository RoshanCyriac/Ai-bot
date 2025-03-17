import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.database.connection import get_conversations_db_connection

# Configure logger
logger = logging.getLogger("reminder-ai.services")

async def save_conversation(conversation_id: Optional[str], user_message: str, ai_response: str) -> str:
    """Save conversation history to the database
    
    Args:
        conversation_id: Optional ID of the conversation
        user_message: The user's message
        ai_response: The AI's response
        
    Returns:
        The conversation ID
    """
    try:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conn = get_conversations_db_connection()
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

async def get_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
    """Get conversation history from the database
    
    Args:
        conversation_id: The ID of the conversation
        
    Returns:
        A list of message dictionaries
    """
    try:
        conn = get_conversations_db_connection()
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