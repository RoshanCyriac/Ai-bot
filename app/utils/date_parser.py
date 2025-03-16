import re
import logging
from datetime import datetime, timedelta

# Configure logger
logger = logging.getLogger("reminder-ai.utils")

def parse_date(date_string: str) -> str:
    """Convert various date formats to a standard format
    
    Args:
        date_string: A string representing a date in various formats
        
    Returns:
        A standardized date string in YYYY-MM-DD format
    """
    try:
        # Handle relative dates
        lower_date = date_string.lower()
        today = datetime.now()
        
        if "today" in lower_date:
            return today.strftime("%Y-%m-%d")
        elif "tomorrow" in lower_date:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in lower_date:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Try to parse month names
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        for month_name, month_num in months.items():
            if month_name in lower_date:
                # Try to extract day
                day_match = re.search(r'\d+', lower_date)
                if day_match:
                    day = int(day_match.group())
                    year = today.year
                    # If the month is earlier than current and day has passed, assume next year
                    if month_num < today.month or (month_num == today.month and day < today.day):
                        year += 1
                    return f"{year}-{month_num:02d}-{day:02d}"
        
        # If all else fails, return the original string
        return date_string
    except Exception as e:
        logger.error(f"Error parsing date: {str(e)}")
        return date_string 