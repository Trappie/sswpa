import sqlite3
import os
from contextlib import contextmanager
import logging
import hashlib
import secrets

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
            
            # Admin password table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logging.info(f"Database initialized at {DATABASE_PATH}")
            
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

def create_recital_schema():
    """Create all recital-related tables if they don't exist"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Recitals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recitals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist_name TEXT NOT NULL,
                    description TEXT,
                    venue TEXT NOT NULL,
                    venue_address TEXT,
                    event_date DATE NOT NULL,
                    event_time TIME NOT NULL,
                    status TEXT DEFAULT 'upcoming',
                    slug TEXT UNIQUE NOT NULL,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ticket types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recital_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    price_cents INTEGER NOT NULL,
                    description TEXT,
                    max_quantity INTEGER DEFAULT 10,
                    total_available INTEGER,
                    sort_order INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recital_id) REFERENCES recitals(id)
                )
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recital_id INTEGER NOT NULL,
                    buyer_email TEXT NOT NULL,
                    buyer_name TEXT NOT NULL,
                    phone TEXT,
                    total_amount_cents INTEGER NOT NULL,
                    payment_status TEXT DEFAULT 'pending',
                    square_payment_id TEXT,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (recital_id) REFERENCES recitals(id)
                )
            """)
            
            # Order items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    ticket_type_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_per_ticket_cents INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id)
                )
            """)
            
            # Donations table (future use)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    donor_email TEXT NOT NULL,
                    donor_name TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    donation_type TEXT DEFAULT 'general',
                    payment_status TEXT DEFAULT 'pending',
                    square_payment_id TEXT,
                    donation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_anonymous BOOLEAN DEFAULT 0,
                    message TEXT
                )
            """)
            
            conn.commit()
            logging.info("Recital schema created successfully")
            return True
            
    except Exception as e:
        logging.error(f"Failed to create recital schema: {e}")
        return False

def check_required_tables() -> dict:
    """Check if all required tables exist"""
    required_tables = {
        'recitals': False,
        'ticket_types': False,
        'orders': False,
        'order_items': False,
        'donations': False,
        'passwords': False,
        'test_data': False
    }
    
    try:
        existing_tables = get_all_table_names()
        for table in required_tables:
            if table in existing_tables:
                required_tables[table] = True
        
        return required_tables
        
    except Exception as e:
        logging.error(f"Failed to check required tables: {e}")
        return required_tables

def ensure_complete_schema() -> tuple:
    """Ensure all required tables exist, create if missing"""
    table_status = check_required_tables()
    missing_tables = [table for table, exists in table_status.items() if not exists]
    
    if missing_tables:
        logging.info(f"Missing tables detected: {missing_tables}")
        # Create recital schema (includes most missing tables)
        if create_recital_schema():
            # Re-check after creation
            table_status = check_required_tables()
            missing_tables = [table for table, exists in table_status.items() if not exists]
            
            if missing_tables:
                return False, f"Failed to create tables: {missing_tables}"
            else:
                return True, f"Successfully created missing tables"
        else:
            return False, "Failed to create recital schema"
    else:
        return True, "All required tables exist"

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

# Admin password functions
def hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with salt. Returns (hash, salt)"""
    if salt is None:
        salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def has_admin_password() -> bool:
    """Check if admin password is set"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM passwords")
        return cursor.fetchone()[0] > 0

def set_admin_password(password: str) -> bool:
    """Set or update admin password"""
    try:
        password_hash, salt = hash_password(password)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Delete old passwords and insert new one
            cursor.execute("DELETE FROM passwords")
            cursor.execute(
                "INSERT INTO passwords (password_hash, salt) VALUES (?, ?)",
                (password_hash, salt)
            )
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Failed to set admin password: {e}")
        return False

def verify_admin_password(password: str) -> bool:
    """Verify admin password"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, salt FROM passwords ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            if not result:
                return False
            
            stored_hash, salt = result
            password_hash, _ = hash_password(password, salt)
            return password_hash == stored_hash
    except Exception as e:
        logging.error(f"Failed to verify admin password: {e}")
        return False

def get_all_table_names() -> list:
    """Get all table names in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

def get_table_data(table_name: str, limit: int = 100) -> list:
    """Get data from any table with limit"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Simple SQL injection prevention - allow alphanumeric and underscore
        if not all(c.isalnum() or c == '_' for c in table_name):
            raise ValueError("Invalid table name")
        
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def execute_custom_query(query: str, limit: int = 100) -> dict:
    """Execute custom SQL query with results limit"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchmany(limit)
                columns = [description[0] for description in cursor.description] if cursor.description else []
                return {
                    "success": True,
                    "results": [dict(zip(columns, row)) for row in results],
                    "columns": columns,
                    "row_count": len(results)
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "message": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                    "row_count": cursor.rowcount
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }