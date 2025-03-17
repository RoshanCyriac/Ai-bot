import sqlite3
import logging
from sqlite3 import Connection, Row

# Configure logger
logger = logging.getLogger("reminder-ai.database")

# Database file paths
REMINDERS_DB_FILE = "reminders.db"
CONVERSATIONS_DB_FILE = "database.db"

def get_db_connection(db_file=REMINDERS_DB_FILE) -> Connection:
    """Get a connection to the SQLite database with row factory
    
    Args:
        db_file: The database file to connect to
        
    Returns:
        A database connection
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def get_conversations_db_connection() -> Connection:
    """Get a connection to the conversations database
    
    Returns:
        A database connection to the conversations database
    """
    return get_db_connection(CONVERSATIONS_DB_FILE)

def init_db() -> None:
    """Initialize the database with required tables"""
    try:
        # Initialize reminders database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create reminders table with additional fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                date TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                tags TEXT DEFAULT '[]',
                completed BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize conversations database
        conn = get_conversations_db_connection()
        cursor = conn.cursor()
        
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
        logger.info("Databases initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# Initialize database on module import
init_db() 