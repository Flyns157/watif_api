"""
This module provides the AuthDatabase class, which manages user authentication data in an SQLite database.
It includes methods for creating and verifying users, as well as hashing and checking passwords.

Classes:
    - AuthDatabase: Manages user creation, password hashing, and authentication checks for a user database.
"""

import sqlite3
import bcrypt

class AuthDatabase:
    """
    AuthDatabase provides methods for managing a user database, including creating user records,
    hashing passwords, and verifying user credentials.

    Attributes:
        conn (sqlite3.Connection): The connection object for the SQLite database.
    """

    def __init__(self, db_name: str = 'database') -> None:
        """
        Initializes the AuthDatabase instance by connecting to the SQLite database and
        creating the users table if it doesn't already exist.
        
        Parameters:
            db_name (str): Name of the SQLite database file.
        """
        try:
            self.conn = sqlite3.connect(db_name)
            if self.conn.execute(""".tables""").fetchone() is None:
                self.create_table()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise

    def __enter__(self):
        """Support with-statement for automatic resource management."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the database connection on exit."""
        self.close()

    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        Hashes a plain-text password using bcrypt.

        Parameters:
            password (str): The plain-text password to hash.

        Returns:
            bytes: The hashed password.
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password: str, hashed: bytes) -> bool:
        """
        Checks a plain-text password against a hashed password.

        Parameters:
            password (str): The plain-text password to verify.
            hashed (bytes): The hashed password to check against.

        Returns:
            bool: True if the password matches the hash, False otherwise.
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def create_table(self) -> None:
        """
        Creates the 'users' table in the database if it does not already exist.
        The table includes columns for a unique username and a hashed password.
        """
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password BLOB NOT NULL
                )
            """)
        self.create_user('admin', 'admin')

    def create_user(self, username: str, password: str) -> bool:
        """
        Adds a new user to the database with a hashed password.

        Parameters:
            username (str): The unique username for the user.
            password (str): The plain-text password for the user.

        Returns:
            bool: True if the user was created successfully, False if the username already exists.
        """
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO users (username, password) VALUES (?, ?)
                """, (username, self.hash_password(password)))
            print(f"User {username} created successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Username {username} already exists.")
            return False
    
    def check_user(self, username: str, password: str) -> bool:
        """
        Verifies a user's credentials by checking if the provided password matches the stored hash.

        Parameters:
            username (str): The username to verify.
            password (str): The plain-text password to check.

        Returns:
            bool: True if the username exists and the password is correct, False otherwise.
        """
        with self.conn:
            cursor = self.conn.execute("""
                SELECT password FROM users WHERE username = ?
            """, (username,))
            result = cursor.fetchone()
            return result is not None and self.check_password(password, result[0])
    
    def exist_user(self, username: str) -> bool:
        """
        Checks if a username exists in the database.

        Parameters:
            username (str): The username to check.

        Returns:
            bool: True if the username exists, False otherwise.
        """
        with self.conn:
            cursor = self.conn.execute("""
                SELECT 1 FROM users WHERE username = ?
            """, (username,))
            return cursor.fetchone() is not None
    
    def close(self) -> None:
        """
        Closes the database connection.
        """
        self.conn.close()
