# database.py
import sqlite3
import json

DB_NAME = "food_delivery.db"

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def create_db_and_tables():
    """Creates the database file and the orders table if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        items TEXT, -- Storing list as a JSON string
        eta TEXT,
        issue_label TEXT,
        resolution_note TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("[Database] Initialized and table 'orders' is ready.")

def create_order(order_id, issue_label, template_data):
    """Creates a new order record in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (order_id, status, items, eta, issue_label, resolution_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        template_data.get('status', 'unknown'),
        json.dumps(template_data.get('items', [])),
        template_data.get('eta'),
        issue_label,
        None
    ))
    conn.commit()
    conn.close()

def get_order(order_id: str) -> dict:
    """Retrieves an order from the database by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order_row = cursor.fetchone()
    conn.close()
    if order_row:
        return dict(order_row)
    return None

def update_order_resolution(order_id: str, note: str):
    """Updates the resolution note for a specific order."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET resolution_note = ? WHERE order_id = ?", (note, order_id))
    conn.commit()
    conn.close()