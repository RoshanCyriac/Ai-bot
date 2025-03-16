import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db-migration")

def migrate_database():
    """Migrate the database schema to match the current code"""
    try:
        # Connect to the database
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(reminders)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add missing columns
        if "priority" not in columns:
            print("Adding 'priority' column")
            cursor.execute("ALTER TABLE reminders ADD COLUMN priority TEXT DEFAULT 'normal'")
        
        if "tags" not in columns:
            print("Adding 'tags' column")
            cursor.execute("ALTER TABLE reminders ADD COLUMN tags TEXT DEFAULT '[]'")
        
        if "completed" not in columns:
            print("Adding 'completed' column")
            cursor.execute("ALTER TABLE reminders ADD COLUMN completed BOOLEAN DEFAULT 0")
        
        # Create conversations table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                messages TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(reminders)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        conn.close()
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Error during database migration: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_database() 