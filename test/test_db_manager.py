from src.database.db_manager import DatabaseConnection

# Create two objects
db1 = DatabaseConnection()
db2 = DatabaseConnection()

# Check whether both refer to the same object
print("Same instance:", db1 is db2)

# Test database connection
connection = db1.get_connection("employee_oltp")

print("Database connected:", connection.is_connected())

connection.close()
print("Connection closed successfully")