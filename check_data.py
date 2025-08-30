import sqlite3
import os

db_path = "app.db"
print("Using database:", db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

cursor.execute("SELECT * FROM users;")
print(cursor.fetchall())

conn.close()
