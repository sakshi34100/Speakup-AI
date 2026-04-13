import hashlib
import sqlite3


# Database connection setup
def create_connection():
    conn = sqlite3.connect("speakup_users.db")
    return conn

# Tables banana (Users aur Leaderboard ke liye)
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    # User Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       username TEXT UNIQUE, 
                       password TEXT)''')
    # Scores Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       username TEXT, 
                       category TEXT, 
                       score INTEGER, 
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Password ko secure rakhne ke liye hashing
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Naya user register karna
def add_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Login check karna
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    data = cursor.fetchone()
    conn.close()
    return data

# Score save karna
def add_score(username, category, score):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scores (username, category, score) VALUES (?,?,?)", (username, category, score))
    conn.commit()
    conn.close()

# Leaderboard ka data nikalna (Top 10)
def get_leaderboard():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, SUM(score) as total_score FROM scores GROUP BY username ORDER BY total_score DESC LIMIT 10")
    data = cursor.fetchall()
    conn.close()
    return data

# Tables initialize karna
create_tables()

# User ke module-wise scores nikalne ke liye
def get_user_module_scores(username):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, score
        FROM scores
        WHERE username = ?
        ORDER BY id DESC
    """, (username,))

    data = cursor.fetchall()
    conn.close()
    return data