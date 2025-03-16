import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.database import get_db_connection
from app.utils import parse_date, format_reminder

# Configure logger
logger = logging.getLogger("reminder-ai.services")

async def add_reminder(message: str, date: str, priority: str = "normal", tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Add a reminder to the database
    
    Args:
        message: The reminder message
        date: The date for the reminder
        priority: The priority level (default: "normal")
        tags: Optional list of tags
        
    Returns:
        A dictionary with the result and formatted reminder
    """
    try:
        if tags is None:
            tags = []
        
        # Parse the date to a standard format
        parsed_date = parse_date(date)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_message, date, priority, tags) VALUES (?, ?, ?, ?)",
            (message, parsed_date, priority, json.dumps(tags))
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        
        # Fetch the inserted reminder
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        conn.close()
        
        formatted_reminder = format_reminder(reminder)
        return {
            "success": True,
            "message": f"✅ Reminder added: {message} on {parsed_date}",
            "reminder": formatted_reminder
        }
    except Exception as e:
        logger.error(f"Error adding reminder: {str(e)}")
        return {
            "success": False,
            "message": f"Error adding reminder: {str(e)}"
        }

async def get_reminders(date_filter: Optional[str] = None, completed: bool = False) -> Dict[str, Any]:
    """Get reminders from the database with optional filtering
    
    Args:
        date_filter: Optional date to filter reminders
        completed: Whether to show completed reminders
        
    Returns:
        A dictionary with the result and formatted reminders
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM reminders WHERE completed = ?"
        params = [1 if completed else 0]
        
        if date_filter:
            query += " AND date = ?"
            params.append(date_filter)
        
        query += " ORDER BY date ASC, priority DESC"
        
        cursor.execute(query, params)
        reminders = cursor.fetchall()
        conn.close()
        
        if not reminders:
            return {
                "success": True,
                "message": "No reminders found" + (f" for {date_filter}" if date_filter else ""),
                "reminders": []
            }
        
        formatted_reminders = [format_reminder(r) for r in reminders]
        
        result_message = "📅 Here are your reminders:\n"
        for r in formatted_reminders:
            priority_icon = "🔴" if r["priority"] == "high" else "🟡" if r["priority"] == "medium" else "🟢"
            result_message += f"{priority_icon} {r['date']}: {r['message']}\n"
        
        return {
            "success": True,
            "message": result_message,
            "reminders": formatted_reminders
        }
    except Exception as e:
        logger.error(f"Error retrieving reminders: {str(e)}")
        return {
            "success": False,
            "message": f"Error retrieving reminders: {str(e)}",
            "reminders": []
        }

async def complete_reminder(reminder_id: int) -> Dict[str, Any]:
    """Mark a reminder as completed
    
    Args:
        reminder_id: The ID of the reminder to mark as completed
        
    Returns:
        A dictionary with the result
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if reminder exists
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            conn.close()
            return {
                "success": False,
                "message": f"Reminder with ID {reminder_id} not found"
            }
        
        # Mark as completed
        cursor.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"✅ Reminder '{reminder['user_message']}' marked as completed"
        }
    except Exception as e:
        logger.error(f"Error completing reminder: {str(e)}")
        return {
            "success": False,
            "message": f"Error completing reminder: {str(e)}"
        }

async def delete_reminder(reminder_id: int) -> Dict[str, Any]:
    """Delete a reminder from the database
    
    Args:
        reminder_id: The ID of the reminder to delete
        
    Returns:
        A dictionary with the result
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if reminder exists
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            conn.close()
            return {
                "success": False,
                "message": f"Reminder with ID {reminder_id} not found"
            }
        
        # Delete the reminder
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"🗑️ Reminder '{reminder['user_message']}' deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting reminder: {str(e)}")
        return {
            "success": False,
            "message": f"Error deleting reminder: {str(e)}"
        }

async def get_upcoming_reminders() -> Dict[str, Any]:
    """Get reminders for today and tomorrow
    
    Returns:
        A dictionary with the result and formatted reminders
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM reminders WHERE date IN (?, ?) AND completed = 0 ORDER BY date ASC, priority DESC",
            (today, tomorrow)
        )
        reminders = cursor.fetchall()
        conn.close()
        
        if not reminders:
            return {
                "success": True,
                "message": "No upcoming reminders for today or tomorrow",
                "reminders": []
            }
        
        formatted_reminders = [format_reminder(r) for r in reminders]
        
        result_message = "⏰ Here are your upcoming reminders:\n"
        for r in formatted_reminders:
            day = "Today" if r["date"] == today else "Tomorrow"
            priority_icon = "🔴" if r["priority"] == "high" else "🟡" if r["priority"] == "medium" else "🟢"
            result_message += f"{priority_icon} {day}: {r['message']}\n"
        
        return {
            "success": True,
            "message": result_message,
            "reminders": formatted_reminders
        }
    except Exception as e:
        logger.error(f"Error retrieving upcoming reminders: {str(e)}")
        return {
            "success": False,
            "message": f"Error retrieving upcoming reminders: {str(e)}",
            "reminders": []
        } 