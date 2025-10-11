import sqlite3
import os

# Get absolute path to the script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go one level up to the project folder
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Create a folder called 'database' inside the project folder
DB_FOLDER = os.path.join(PROJECT_DIR, "database")
os.makedirs(DB_FOLDER, exist_ok=True)

# Full path to database file
DB_PATH = os.path.join(DB_FOLDER, "campus_companion.db")

def insert_course(name, credits, grade):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO courses (name, credits, grade) VALUES (?, ?, ?)",
        (name, credits, grade)
    )
    con.commit()
    con.close()

def fetch_courses():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM courses")
    rows = cur.fetchall()
    con.close()
    return rows

def connect_db():
    print(f"🔗 Connecting to database at: '{DB_PATH}'")  # debug message
    return sqlite3.connect(DB_PATH)

def init_db():
    con = connect_db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            credits INTEGER,
            grade TEXT
        )
    """)
    con.commit()
    con.close()