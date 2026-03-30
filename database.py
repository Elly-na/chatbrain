import sqlite3
from datetime import datetime
import bcrypt

class ChatDatabase:
    def __init__(self, db_name='chats.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Users table — added email column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Chats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                text TEXT NOT NULL,
                commands TEXT,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id)
            )
        ''')

        # Default admin user
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password))

        conn.commit()
        conn.close()

    def verify_user(self, username, password):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            return user[0]
        return None

    def create_user(self, username, password, email=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def create_chat(self, user_id, name):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chats (user_id, name) VALUES (?, ?)", (user_id, name))
        chat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return chat_id

    def get_user_chats(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, created_at, updated_at
            FROM chats
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        chats = cursor.fetchall()
        conn.close()
        return [{'id': c[0], 'name': c[1], 'created_at': c[2], 'updated_at': c[3]} for c in chats]

    def add_message(self, chat_id, msg_type, text, commands=None, explanation=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (chat_id, type, text, commands, explanation)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, msg_type, text, commands, explanation))
        cursor.execute("UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (chat_id,))
        conn.commit()
        conn.close()

    def get_chat_messages(self, chat_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, text, commands, explanation, created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
        ''', (chat_id,))
        messages = cursor.fetchall()
        conn.close()
        return [{'type': m[0], 'text': m[1], 'commands': m[2], 'explanation': m[3], 'created_at': m[4]} for m in messages]

    def rename_chat(self, chat_id, new_name):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE chats SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_name, chat_id))
        conn.commit()
        conn.close()

    def delete_chat(self, chat_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        conn.close()