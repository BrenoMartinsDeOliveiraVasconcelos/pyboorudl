import sqlite3
import keyring

class Credential:
    def __init__(self, db_path="credentials.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booru TEXT NOT NULL,
                username TEXT NOT NULL,
                user_id TEXT,
                UNIQUE(booru, username)
            )
        """)
        self.conn.commit()

    def _get_service_name(self, booru: str) -> str:
        """Helper to create a unique service name for the OS credential manager"""
        return f"pyboorudl_{booru}"

    def add_credential(self, booru: str, username: str, api_key: str = "", user_id: str = ""):
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO credentials (booru, username, user_id)
                VALUES (?, ?, ?)
            """, (booru, username, user_id))
            self.conn.commit()

            if api_key:
                keyring.set_password(self._get_service_name(booru), username, api_key)
            
            return True
        except Exception as e:
            print(f"Error while adding credential: {e}")
            return False

    def remove_credential(self, booru: str, username: str):
        try:
            self.cursor.execute("""
                DELETE FROM credentials 
                WHERE booru = ? AND username = ?
            """, (booru, username))
            self.conn.commit()
            
            try:
                keyring.delete_password(self._get_service_name(booru), username)
            except keyring.errors.PasswordDeleteError:
                pass # It's not there??? ok

            return True
        except Exception as e:
            print(f"Error while removing credential: {e}")
            return False

    def get_credential(self, booru: str, username: str) -> tuple:
        """Returns a tuple: (api_key, user_id) or None if not found."""
        self.cursor.execute("""
            SELECT user_id FROM credentials 
            WHERE booru = ? AND username = ?
        """, (booru, username))
        
        row = self.cursor.fetchone()
        if row:
            user_id = row[0]
            api_key = keyring.get_password(self._get_service_name(booru), username) or ""
            return (api_key, user_id)
        
        return None

    def close(self):
        self.conn.close()


if __name__== '__main__':
    print("This is no script!")