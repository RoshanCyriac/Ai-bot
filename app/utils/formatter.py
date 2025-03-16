import json
from typing import Dict, Any, List

def format_reminder(reminder: Dict[str, Any]) -> Dict[str, Any]:
    """Format a reminder row as a dictionary
    
    Args:
        reminder: A SQLite Row object representing a reminder
        
    Returns:
        A formatted dictionary with reminder data
    """
    try:
        tags = json.loads(reminder["tags"])
    except:
        tags = []
    
    return {
        "id": reminder["id"],
        "message": reminder["user_message"],
        "date": reminder["date"],
        "priority": reminder["priority"],
        "tags": tags,
        "completed": bool(reminder["completed"])
    } 