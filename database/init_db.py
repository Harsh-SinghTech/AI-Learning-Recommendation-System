import sqlite3

conn = sqlite3.connect("database/ai_learning.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    full_name TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    interest TEXT,

    skill_level TEXT

)
""")

conn.commit()

conn.close()

print("Database created successfully!")