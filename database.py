import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "insta_lite.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db", "schema.sql")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_context():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        return

    with get_db_context() as conn:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.commit()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
