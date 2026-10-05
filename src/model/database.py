"""
Database model for calculation history.
Uses SQLite for simplicity.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'calculator.db')


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database table."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expression TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def add_record(expression: str, result: str) -> int:
    """Add a new calculation record. Returns the new record ID."""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO calculation_history (expression, result, created_at) VALUES (?, ?, ?)',
        (expression, result, now)
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_all_records() -> List[Dict]:
    """Get all calculation history records, newest first."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, expression, result, created_at FROM calculation_history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_record(record_id: int) -> bool:
    """Delete a specific record by ID. Returns True if deleted."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM calculation_history WHERE id = ?', (record_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def clear_all_records() -> int:
    """Delete all records. Returns number of rows deleted."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM calculation_history')
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count
