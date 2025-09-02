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

# Recital CRUD operations
def get_recitals(include_past: bool = False) -> list:
    """Get all recitals, optionally including past ones"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if include_past:
            cursor.execute("SELECT * FROM recitals ORDER BY event_date DESC")
        else:
            cursor.execute("SELECT * FROM recitals WHERE status != 'past' ORDER BY event_date ASC")
        return [dict(row) for row in cursor.fetchall()]

def get_recital_by_id(recital_id: int) -> dict:
    """Get a single recital by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recitals WHERE id = ?", (recital_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

def get_recital_by_slug(slug: str) -> dict:
    """Get a single recital by slug"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recitals WHERE slug = ?", (slug,))
        result = cursor.fetchone()
        return dict(result) if result else None

def create_recital(recital_data: dict) -> int:
    """Create a new recital with default ticket types"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create the recital
            cursor.execute("""
                INSERT INTO recitals (
                    title, artist_name, description, venue, venue_address,
                    event_date, event_time, status, slug, image_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recital_data['title'], recital_data['artist_name'], recital_data.get('description'),
                recital_data['venue'], recital_data.get('venue_address'),
                recital_data['event_date'], recital_data['event_time'],
                recital_data.get('status', 'upcoming'), recital_data['slug'],
                recital_data.get('image_url')
            ))
            
            recital_id = cursor.lastrowid
            
            # Create default ticket types
            default_tickets = [
                {
                    'name': 'Adult',
                    'price_cents': 2500,  # $25.00
                    'description': 'General admission for adults',
                    'max_quantity': 10,
                    'sort_order': 1,
                    'active': 1
                },
                {
                    'name': 'Student',
                    'price_cents': 1000,  # $10.00
                    'description': 'Student discount',
                    'max_quantity': 10,
                    'sort_order': 2,
                    'active': 1
                }
            ]
            
            for ticket in default_tickets:
                cursor.execute("""
                    INSERT INTO ticket_types (
                        recital_id, name, price_cents, description, max_quantity,
                        total_available, sort_order, active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recital_id, ticket['name'], ticket['price_cents'],
                    ticket['description'], ticket['max_quantity'],
                    None,  # unlimited availability
                    ticket['sort_order'], ticket['active']
                ))
            
            conn.commit()
            logging.info(f"Created recital {recital_id} with default ticket types")
            return recital_id
            
    except Exception as e:
        logging.error(f"Failed to create recital: {e}")
        return False

def update_recital(recital_id: int, recital_data: dict) -> bool:
    """Update an existing recital"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE recitals SET
                    title = ?, artist_name = ?, description = ?, venue = ?, venue_address = ?,
                    event_date = ?, event_time = ?, status = ?, slug = ?, image_url = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                recital_data['title'], recital_data['artist_name'], recital_data.get('description'),
                recital_data['venue'], recital_data.get('venue_address'),
                recital_data['event_date'], recital_data['event_time'],
                recital_data.get('status', 'upcoming'), recital_data['slug'],
                recital_data.get('image_url'), recital_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logging.error(f"Failed to update recital: {e}")
        return False

def delete_recital(recital_id: int) -> bool:
    """Delete a recital and its related data"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Delete in order: order_items -> orders -> ticket_types -> recitals
            cursor.execute("""
                DELETE FROM order_items WHERE ticket_type_id IN 
                (SELECT id FROM ticket_types WHERE recital_id = ?)
            """, (recital_id,))
            cursor.execute("DELETE FROM orders WHERE recital_id = ?", (recital_id,))
            cursor.execute("DELETE FROM ticket_types WHERE recital_id = ?", (recital_id,))
            cursor.execute("DELETE FROM recitals WHERE id = ?", (recital_id,))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Failed to delete recital: {e}")
        return False

# Ticket Type CRUD operations
def get_ticket_types_for_recital(recital_id: int) -> list:
    """Get all ticket types for a specific recital"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tt.*, r.title as recital_title 
            FROM ticket_types tt
            JOIN recitals r ON tt.recital_id = r.id
            WHERE tt.recital_id = ? 
            ORDER BY tt.sort_order ASC
        """, (recital_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_ticket_type_by_id(ticket_type_id: int) -> dict:
    """Get a single ticket type by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tt.*, r.title as recital_title 
            FROM ticket_types tt
            JOIN recitals r ON tt.recital_id = r.id
            WHERE tt.id = ?
        """, (ticket_type_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

def create_ticket_type(ticket_data: dict) -> int:
    """Create a new ticket type"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ticket_types (
                    recital_id, name, price_cents, description, max_quantity,
                    total_available, sort_order, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_data['recital_id'], ticket_data['name'], ticket_data['price_cents'],
                ticket_data.get('description'), ticket_data.get('max_quantity', 10),
                ticket_data.get('total_available'), ticket_data.get('sort_order', 0),
                ticket_data.get('active', 1)
            ))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logging.error(f"Failed to create ticket type: {e}")
        return False

def update_ticket_type(ticket_type_id: int, ticket_data: dict) -> bool:
    """Update an existing ticket type"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ticket_types SET
                    recital_id = ?, name = ?, price_cents = ?, description = ?,
                    max_quantity = ?, total_available = ?, sort_order = ?, active = ?
                WHERE id = ?
            """, (
                ticket_data['recital_id'], ticket_data['name'], ticket_data['price_cents'],
                ticket_data.get('description'), ticket_data.get('max_quantity', 10),
                ticket_data.get('total_available'), ticket_data.get('sort_order', 0),
                ticket_data.get('active', 1), ticket_type_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logging.error(f"Failed to update ticket type: {e}")
        return False

def delete_ticket_type(ticket_type_id: int) -> bool:
    """Delete a ticket type and its related order items"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Delete order items first, then ticket type
            cursor.execute("DELETE FROM order_items WHERE ticket_type_id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_types WHERE id = ?", (ticket_type_id,))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Failed to delete ticket type: {e}")
        return False