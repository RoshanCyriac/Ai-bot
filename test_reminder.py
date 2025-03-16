import asyncio
import json
from app.gemini.client import process_with_gemini
from app.gemini.tools import create_gemini_tools
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-reminder")

async def test_reminder():
    # Test message
    user_message = "Remind me to call mom tomorrow"
    
    logger.info(f"Testing reminder with message: {user_message}")
    
    # Get tools
    tools = create_gemini_tools()
    logger.info(f"Tools: {json.dumps(tools, indent=2)}")
    
    # Process with Gemini
    response = await process_with_gemini(user_message)
    
    logger.info(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_reminder()) 