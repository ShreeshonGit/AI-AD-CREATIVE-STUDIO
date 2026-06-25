import os
import json
import sqlite3
from datetime import datetime

# Resolve absolute path to database location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATABASE_DIR = os.path.join(BACKEND_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "generations.db")

def init_db() -> None:
    """
    Initializes the generations.db SQLite database and creates the generations table if it does not exist.
    """
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            category TEXT,
            audience TEXT,
            generated_output TEXT,
            compliance_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    conn.close()

def save_generation(
    product_name: str,
    category: str,
    audience: str,
    generated_output_dict: dict,
    compliance_status: str
) -> int:
    """
    Saves a generation event and its output details in SQLite, returning the row id.
    """
    # Ensure database is initialized
    init_db()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    output_json = json.dumps(generated_output_dict, ensure_ascii=False)
    
    cursor.execute(
        """
        INSERT INTO generations (product_name, category, audience, generated_output, compliance_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            product_name,
            category,
            audience,
            output_json,
            compliance_status,
            datetime.now().isoformat()
        )
    )
    
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id
