
import os
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


# Load database credentials from .env
load_dotenv()


class DatabaseConnection:

    # Stores the single instance of this class
    _instance = None

    def __new__(cls):
        # Create the object only once
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        # Avoid initializing the same instance multiple times
        if not hasattr(self, "host"):
            self.host = os.getenv("DB_HOST")
            self.port = int(os.getenv("DB_PORT", 3306))
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")

    def get_connection(self, database_name):
        try:
            # Connect to the requested database
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=database_name
            )

            return connection

        except Error as e:
            print("Database connection failed:", e)
            raise
