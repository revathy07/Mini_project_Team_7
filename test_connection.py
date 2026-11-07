import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

conn = mysql.connector.connect(
    host = os.getenv("DB_HOST"),
    port = int(os.getenv("DB_PORT", 3306)),
    user = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
)

print("Connected. MySQL version;", conn.server_info)
conn.close()