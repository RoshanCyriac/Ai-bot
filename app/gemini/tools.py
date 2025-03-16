from typing import List, Dict, Any

def create_gemini_tools() -> List[Dict[str, Any]]:
    """Create tools definition for Gemini
    
    Returns:
        A list of tool definitions for Gemini
    """
    return [
        {
            "name": "add_reminder",
            "description": "Add a new reminder with a date, priority, and optional tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The reminder message content"
                    },
                    "date": {
                        "type": "string",
                        "description": "The date for the reminder (can be a specific date like '2023-12-25' or relative like 'tomorrow', 'next week', 'April 15')"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "medium", "high"],
                        "description": "The priority level of the reminder"
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional tags to categorize the reminder"
                    }
                },
                "required": ["message", "date"]
            }
        },
        {
            "name": "get_reminders",
            "description": "Get all reminders, optionally filtered by date",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optional date filter (e.g., 'today', 'tomorrow', '2023-12-25')"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Whether to show completed reminders (default: false)"
                    }
                }
            }
        },
        {
            "name": "complete_reminder",
            "description": "Mark a reminder as completed",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "The ID of the reminder to mark as completed"
                    }
                },
                "required": ["reminder_id"]
            }
        },
        {
            "name": "delete_reminder",
            "description": "Delete a reminder",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "The ID of the reminder to delete"
                    }
                },
                "required": ["reminder_id"]
            }
        },
        {
            "name": "get_upcoming_reminders",
            "description": "Get reminders for today and tomorrow",
            "parameters": {
                "type": "object",
                "properties": {
                    "dummy": {
                        "type": "string",
                        "description": "This parameter is not used but is required for the API"
                    }
                }
            }
        }
    ] 