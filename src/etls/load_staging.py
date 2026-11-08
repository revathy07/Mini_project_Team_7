import os
import sys
import time
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

CHUNK_ROWS = 20_000

# csv file -> staging table (load order is irrelevant: no FKs)
TABLES = {
    "departments.csv": "stg_departments",
    "employees.csv": "stg_employees",
    "projects.csv": "stg_projects",
    "project_assignments.csv": "stg_project_assignments",
    "performance_reviews.csv": "stg_performance_reviews",
    "employee_changes.csv": "stg_employee_changes",
}


class StagingLoader:
    """Truncate-and-reload each staging table from its CSV, then reconcile counts."""

    def __init__(self, data_dir: Path = Path("data/processed")):
        load_dotenv()
        self.data_dir = data_dir
        self.conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_STAGING", "employee_staging"),
        )

    def load_table(self, csv_name: str, table: str) -> tuple[int, int]:
        path = self.data_dir / csv_name
        if not path.exists():
            raise FileNotFoundError(f"{path} not found - run the synthesizer first")

        cur = self.conn.cursor()
        cur.execute(f"TRUNCATE TABLE {table}")

        csv_rows = 0
        for chunk in pd.read_csv(path, dtype=str, chunksize=CHUNK_ROWS):
            cols = ", ".join(f"`{c}`" for c in chunk.columns)
            marks = ", ".join(["%s"] * len(chunk.columns))
            sql = f"INSERT INTO {table} ({cols}) VALUES ({marks})"
            chunk = chunk.astype(object).where(chunk.notna(), None)  # NaN -> NULL
            cur.executemany(sql, chunk.values.tolist())
            csv_rows += len(chunk)

        self.conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        db_rows = cur.fetchone()[0]
        cur.close()
        return csv_rows, db_rows

    def run(self) -> bool:
        ok = True
        print(f"{'table':28s} {'csv rows':>10s} {'db rows':>10s}  status   time")
        for csv_name, table in TABLES.items():
            t0 = time.time()
            try:
                csv_rows, db_rows = self.load_table(csv_name, table)
            except Exception as err:
                self.conn.rollback()
                print(f"{table:28s} FAILED: {err}")
                return False
            match = csv_rows == db_rows
            ok &= match
            print(f"{table:28s} {csv_rows:>10,} {db_rows:>10,}  "
                  f"{'OK' if match else 'MISMATCH':8s} {time.time() - t0:.1f}s")
        self.conn.close()
        return ok


if __name__ == "__main__":
    sys.exit(0 if StagingLoader().run() else 1)