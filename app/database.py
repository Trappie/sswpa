import sqlite3
import os
from contextlib import contextmanager
import logging

# Database file path from environment variable, default to /data/sswpa.db
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/sswpa.db")

def init_database():
    """Initialize database with basic test table"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Simple test table for now
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logging.info(f"Database initialized at {DATABASE_PATH}")
            
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def write_test_data(message: str) -> int:
    """Write test data to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO test_data (message) VALUES (?)", (message,))
        conn.commit()
        return cursor.lastrowid

def get_test_data():
    """Get all test data from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_data ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]