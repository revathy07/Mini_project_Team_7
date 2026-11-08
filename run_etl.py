import os
from dotenv import load_dotenv
import mysql.connector
import time

load_dotenv()

# Connect to MySQL DW
print("Connecting to MySQL...")
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database="employee_dw"
)

cursor = conn.cursor()

# The list of ETL procedures to run
procedures = [
    "sp_load_dim_date",
    "sp_load_dim_department",
    "sp_load_dim_project",
    "sp_load_fact_performance",
    "sp_load_fact_project_allocations"
]

print("Starting ETL process. This may take a minute or two...\n")

for proc in procedures:
    print(f"Executing {proc}()...")
    start_time = time.time()
    try:
        # Using execute instead of callproc to avoid cursor buffer issues
        cursor.execute(f"CALL {proc}()")
        conn.commit()
        elapsed = time.time() - start_time
        print(f" Success! Took {elapsed:.2f} seconds.\n")
    except mysql.connector.Error as err:
        print(f" Error in {proc}: {err}\n")

cursor.close()
conn.close()

print(" ETL Process Complete!")