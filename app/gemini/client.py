import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

import google.generativeai as genai

from app.gemini.tools import create_gemini_tools
from app.services import (
    add_reminder,
    get_reminders,
    complete_reminder,
    delete_reminder,
    get_upcoming_reminders
)

# Load environment variables from .env file
load_dotenv()

# Configure logger
logger = logging.getLogger("reminder-ai.gemini")

# Set up Google Gemini AI
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# System prompt for Gemini
SYSTEM_PROMPT = """
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

async def process_with_gemini(user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Process user message with Gemini AI and tools
    
    Args:
        user_message: The user's message
        conversation_history: Optional conversation history
        
    Returns:
        The AI's response
    """
    try:
        # Initialize model with tools
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
        
        # Add system prompt first
        messages.append({"role": "user", "parts": [SYSTEM_PROMPT]})
        messages.append({"role": "model", "parts": ["I understand. I'll help with reminders and tasks."]})
        
        # Add conversation history if available
        if conversation_history:
            logger.info(f"Including conversation history with {len(conversation_history)} messages")
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})
        
        # Add current user message
        messages.append({"role": "user", "parts": [user_message]})
        
        logger.info(f"Sending message with {len(messages)} context messages")
        
        # First try without tools to see if we can extract function call from text
        logger.info("Trying without tools first to extract function call from text...")
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
        
        logger.info(f"Response text: {response_text}")
        
        # Check for function call in text
        if response_text:
            # Look for add_reminder function call
            if "add_reminder" in response_text:
                import re
                # Extract parameters from text
                message_match = re.search(r'message\s*=\s*["\']([^"\']+)["\']', response_text)
                date_match = re.search(r'date\s*=\s*["\']([^"\']+)["\']', response_text)
                priority_match = re.search(r'priority\s*=\s*["\']([^"\']+)["\']', response_text)
                
                if message_match and date_match:
                    message = message_match.group(1)
                    date = date_match.group(1)
                    priority = priority_match.group(1) if priority_match else "normal"
                    
                    logger.info(f"Extracted reminder: message={message}, date={date}, priority={priority}")
                    
                    # Call add_reminder service
                    result = await add_reminder(message, date, priority, [])
                    return result.get("message")
            
            # Look for get_reminders function call
            elif any(keyword in response_text.lower() for keyword in ["get_reminders", "show reminders", "list reminders"]):
                date = None
                completed = False
                
                # Check for date in text
                if "today" in response_text.lower():
                    date = "today"
                elif "tomorrow" in response_text.lower():
                    date = "tomorrow"
                
                # Check for completed status
                if "completed" in response_text.lower():
                    completed = True
                
                logger.info(f"Getting reminders with date={date}, completed={completed}")
                
                # Call get_reminders service
                result = await get_reminders(date, completed)
                return result.get("message")
            
            # Look for complete_reminder function call
            elif "complete_reminder" in response_text or "mark as complete" in response_text.lower():
                import re
                reminder_id_match = re.search(r'reminder_id\s*=\s*(\d+)', response_text)
                
                if reminder_id_match:
                    reminder_id = int(reminder_id_match.group(1))
                    logger.info(f"Completing reminder with ID: {reminder_id}")
                    
                    # Call complete_reminder service
                    result = await complete_reminder(reminder_id)
                    return result.get("message")
            
            # Look for delete_reminder function call
            elif "delete_reminder" in response_text or "delete reminder" in response_text.lower():
                import re
                reminder_id_match = re.search(r'reminder_id\s*=\s*(\d+)', response_text)
                
                if reminder_id_match:
                    reminder_id = int(reminder_id_match.group(1))
                    logger.info(f"Deleting reminder with ID: {reminder_id}")
                    
                    # Call delete_reminder service
                    result = await delete_reminder(reminder_id)
                    return result.get("message")
            
            # Look for get_upcoming_reminders function call
            elif "get_upcoming_reminders" in response_text or "upcoming reminders" in response_text.lower():
                logger.info("Getting upcoming reminders")
                
                # Call get_upcoming_reminders service
                result = await get_upcoming_reminders()
                return result.get("message")
        
        # If we couldn't extract a function call, return the response text
        if "remind" in user_message.lower() and "tomorrow" in user_message.lower():
            # Extract the task from the message
            task = user_message.lower().replace("remind me to", "").replace("tomorrow", "").strip()
            if task:
                logger.info(f"Extracted task from message: {task}")
                result = await add_reminder(task, "tomorrow", "normal", [])
                return result.get("message")
        
        # If all else fails, return the model's response
        return response_text or "I'm sorry, I couldn't process your request. Please try rephrasing your message."
    
    except Exception as e:
        logger.error(f"Error processing with Gemini: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}"

async def try_gemini_with_tools(model, messages, tools) -> Tuple[Any, Optional[str]]:
    """Try different methods to call Gemini with tools
    
    Args:
        model: The Gemini model
        messages: The conversation messages
        tools: The tools definition
        
    Returns:
        A tuple of (function_call, response_text)
    """
    function_call = None
    response_text = None
    
    # Try the first format (preferred)
    try:
        # Format tools correctly for function calling
        formatted_tools = tools
        
        response = model.generate_content(
            messages,
            tools=formatted_tools,
            tool_config={"function_calling": "auto"}
        )
        
        logger.info(f"Response type: {type(response)}")
        
        # Check if the model wants to call a function
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        logger.info(f"Function call detected: {function_call.name}")
                        break
                    elif hasattr(part, 'text'):
                        response_text = part.text
        
        logger.info("Successfully processed with first format")
        
    except Exception as e1:
        logger.warning(f"First attempt failed: {str(e1)}")
        
        # Try the second format
        try:
            response = model.generate_content(
                messages,
                tools=[{"function_declarations": tools}]
            )
            
            # Check if the model wants to call a function
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            function_call = part.function_call
                            logger.info(f"Function call detected (second format): {function_call.name}")
                            break
                        elif hasattr(part, 'text'):
                            response_text = part.text
            
            logger.info("Successfully processed with second format")
            
        except Exception as e2:
            logger.warning(f"Second attempt failed: {str(e2)}")
            
            # Try a third format
            try:
                response = model.generate_content(
                    messages,
                    tools=tools
                )
                
                # Check for function call
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_call = part.function_call
                                logger.info(f"Function call detected (third format): {function_call.name}")
                                break
                            elif hasattr(part, 'text'):
                                response_text = part.text
                
                logger.info("Successfully processed with third format")
                
            except Exception as e3:
                logger.warning(f"Third attempt failed: {str(e3)}")
                
                # Fall back to no tools as a last resort
                try:
                    response = model.generate_content(messages)
                    
                    if hasattr(response, 'text'):
                        response_text = response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    response_text = part.text
                    
                    logger.info("Successfully processed without tools")
                    
                except Exception as e4:
                    logger.error(f"All attempts failed: {str(e4)}")
                    return None, "I'm sorry, I'm having trouble processing your request right now. Please try again later."
    
    # If we have response text but no function call, check for function call in text
    if response_text and not function_call:
        logger.info(f"Checking text for function call: {response_text[:100]}...")
        
        # Look for function call pattern in text
        import re
        function_match = re.search(r'add_reminder\(.*?\)', response_text, re.DOTALL)
        if function_match:
            function_text = function_match.group(0)
            logger.info(f"Found function call in text: {function_text}")
            
            # Extract function name and arguments
            try:
                function_name = "add_reminder"
                args_text = function_text.replace("add_reminder(", "").rstrip(")")
                
                # Parse arguments
                args_dict = {}
                for arg_pair in args_text.split(","):
                    if "=" in arg_pair:
                        key, value = arg_pair.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        args_dict[key] = value
                
                # Create a simple function call object
                class FunctionCall:
                    def __init__(self, name, args):
                        self.name = name
                        self.args = args
                
                function_call = FunctionCall(function_name, json.dumps(args_dict))
                logger.info(f"Created function call from text: {function_name} with args {args_dict}")
            except Exception as e:
                logger.error(f"Failed to parse function call from text: {str(e)}")
    
    return function_call, response_text

def extract_function_args(function_call) -> Dict[str, Any]:
    """Extract function arguments from a function call object
    
    Args:
        function_call: The function call object
        
    Returns:
        A dictionary of function arguments
    """
    try:
        # First try direct JSON parsing
        if isinstance(function_call.args, str):
            try:
                function_args = json.loads(function_call.args)
                logger.info(f"Extracted args via JSON parsing: {function_args}")
                return function_args
            except json.JSONDecodeError:
                logger.warning("Failed to parse args as JSON")
                # If it's a string but not valid JSON, try to parse it as a key=value string
                if "=" in function_call.args:
                    args_dict = {}
                    for arg_pair in function_call.args.split(","):
                        if "=" in arg_pair:
                            key, value = arg_pair.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            args_dict[key] = value
                    logger.info(f"Extracted args via key=value parsing: {args_dict}")
                    return args_dict
        
        # If that fails, try handling MapComposite objects
        try:
            # Initialize empty dict for arguments
            function_args = {}
            
            # Check if it has _pb attribute (MapComposite structure)
            if hasattr(function_call.args, '_pb'):
                pb_dict = function_call.args._pb
                
                # Extract values from the nested structure
                for key, value in pb_dict.items():
                    # Extract the actual string value from the protobuf structure
                    if hasattr(value, 'string_value') and value.string_value:
                        function_args[key] = value.string_value
                    elif hasattr(value, 'bool_value'):
                        function_args[key] = value.bool_value
                    elif hasattr(value, 'number_value'):
                        function_args[key] = value.number_value
                    elif hasattr(value, 'list_value') and hasattr(value.list_value, 'values'):
                        # Handle list values
                        function_args[key] = [
                            v.string_value if hasattr(v, 'string_value') else v 
                            for v in value.list_value.values
                        ]
            # If no _pb attribute, try __dict__ or dict() conversion
            elif hasattr(function_call.args, '__dict__'):
                function_args = function_call.args.__dict__
            else:
                function_args = dict(function_call.args)
            
            logger.info(f"Extracted args via object attributes: {function_args}")
            return function_args
                
        except Exception as e:
            logger.error(f"Failed to extract function args from MapComposite: {str(e)}")
            return {}
    
    except Exception as e:
        logger.error(f"Failed to extract function args: {str(e)}")
        return {} 