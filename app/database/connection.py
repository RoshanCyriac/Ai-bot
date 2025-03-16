import sqlite3
import logging
from sqlite3 import Connection, Row

# Configure logger
logger = logging.getLogger("reminder-ai.database")

# Database file path
DB_FILE = "reminders.db"

def get_db_connection() -> Connection:
    """Get a connection to the SQLite database with row factory"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize the database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create reminders table with additional fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                date TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                tags TEXT DEFAULT '[]',
                completed BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create conversation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                messages TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# Initialize database on module import
init_db() 