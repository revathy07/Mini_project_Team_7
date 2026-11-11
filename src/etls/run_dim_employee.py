import os
import sys
import time

import mysql.connector
from dotenv import load_dotenv

STG, OLTP = "employee_staging", "employee_oltp"

# Each query returns (actual, expected); the check passes when they are equal
CHECKS = {
    "row count = history rows + employees without history":
        f"SELECT (SELECT COUNT(*) FROM Dim_Employee), "
        f"(SELECT COUNT(*) FROM {STG}.stg_employee_changes) + "
        f"(SELECT COUNT(*) FROM {OLTP}.Employees WHERE employee_id NOT IN "
        f"  (SELECT employee_id FROM {STG}.stg_employee_changes))",
    "exactly one current row per employee":
        "SELECT COUNT(*), COUNT(DISTINCT employee_code) FROM Dim_Employee WHERE is_current = 1",
    "every employee has a current row":
        f"SELECT (SELECT COUNT(DISTINCT employee_code) FROM Dim_Employee WHERE is_current = 1), "
        f"(SELECT COUNT(*) FROM {OLTP}.Employees)",
    "current rows have end_date 9999-12-31":
        "SELECT COUNT(*), 0 FROM Dim_Employee WHERE is_current = 1 AND end_date <> '9999-12-31'",
    "closed rows have a real end_date":
        "SELECT COUNT(*), 0 FROM Dim_Employee WHERE is_current = 0 AND end_date = '9999-12-31'",
    "no gaps or overlaps (end == next start)":
        "SELECT COUNT(*), 0 FROM (SELECT end_date, "
        "  LEAD(start_date) OVER (PARTITION BY employee_code ORDER BY start_date) AS next_start "
        "  FROM Dim_Employee) t WHERE next_start IS NOT NULL AND end_date <> next_start",
    "no zero/negative-length windows":
        "SELECT COUNT(*), 0 FROM Dim_Employee WHERE end_date <= start_date",
    "first version starts at hire date":
        "SELECT COUNT(*), 0 FROM (SELECT hire_date, start_date, "
        "  ROW_NUMBER() OVER (PARTITION BY employee_code ORDER BY start_date) AS rn "
        "  FROM Dim_Employee) t WHERE rn = 1 AND start_date <> hire_date",
    "current row matches OLTP":
        f"SELECT COUNT(*), 0 FROM Dim_Employee d "
        f"JOIN {OLTP}.Employees e ON e.employee_code = d.employee_code "
        f"JOIN {OLTP}.Departments dp ON dp.department_id = e.department_id "
        f"WHERE d.is_current = 1 AND (d.department_name <> dp.department_name "
        f"  OR d.job_role <> e.job_role OR d.job_level <> e.job_level "
        f"  OR d.monthly_income <> e.monthly_income)",
}


def main() -> bool:
    load_dotenv()
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DW", "employee_dw"),

        # Aiven SSL configuration
        ssl_ca=os.getenv("DB_SSL_CA") or None,
        ssl_verify_cert=bool(os.getenv("DB_SSL_CA")),
)
    cur = conn.cursor()

    print("Running sp_load_dim_employee_history() ...")
    t0 = time.time()
    try:
        cur.execute("CALL sp_load_dim_employee_history()")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"ETL FAILED: {err}")
        return False
    print(f"Loaded in {time.time() - t0:.1f}s\n")

    ok = True
    print(f"{'check':54s} {'actual':>10s} {'expected':>10s}")
    for label, sql in CHECKS.items():
        cur.execute(sql)
        actual, expected = cur.fetchone()
        passed = actual == expected
        ok &= passed
        print(f"{'PASS' if passed else 'FAIL'}  {label:48s} {actual:>10,} {expected:>10,}")

    cur.close()
    conn.close()
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)