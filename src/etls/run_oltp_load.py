import os
import sys
import time

import mysql.connector
from dotenv import load_dotenv

STG, OLTP = "employee_staging", "employee_oltp"

# Each query returns (actual, expected); the check passes when they are equal
CHECKS = {
    "departments row count":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Departments), (SELECT COUNT(*) FROM {STG}.stg_departments)",
    "employees row count":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Employees), (SELECT COUNT(*) FROM {STG}.stg_employees)",
    "projects row count":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Projects), (SELECT COUNT(*) FROM {STG}.stg_projects)",
    "assignments row count":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Project_Assignments), (SELECT COUNT(*) FROM {STG}.stg_project_assignments)",
    "reviews row count (none dropped)":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Performance_Reviews), (SELECT COUNT(*) FROM {STG}.stg_performance_reviews)",
    "change events (distinct employee+date)":
        f"SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT employee_id, change_date FROM {OLTP}.Employee_Change_Log) t), "
        f"(SELECT COUNT(*) FROM {STG}.stg_employee_changes WHERE version_no > 1)",
    "terminated status == termination dates":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Employees WHERE status = 'Terminated'), "
        f"(SELECT COUNT(*) FROM {STG}.stg_employees WHERE termination_date IS NOT NULL)",
    "completed assignments == released dates":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Project_Assignments WHERE status = 'Completed'), "
        f"(SELECT COUNT(*) FROM {STG}.stg_project_assignments WHERE released_date IS NOT NULL)",
    "every department has a head":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Departments WHERE manager_id IS NOT NULL), "
        f"(SELECT COUNT(*) FROM {OLTP}.Departments)",
    # ---- orphans (FK checks were off during the load) ----
    "orphan employee managers":
        f"SELECT COUNT(*), 0 FROM {OLTP}.Employees e LEFT JOIN {OLTP}.Employees m "
        f"ON e.manager_id = m.employee_id WHERE e.manager_id IS NOT NULL AND m.employee_id IS NULL",
    "orphan employee departments":
        f"SELECT COUNT(*), 0 FROM {OLTP}.Employees e LEFT JOIN {OLTP}.Departments d "
        f"ON e.department_id = d.department_id WHERE d.department_id IS NULL",
    "orphan assignments":
        f"SELECT COUNT(*), 0 FROM {OLTP}.Project_Assignments a "
        f"LEFT JOIN {OLTP}.Employees e ON a.employee_id = e.employee_id "
        f"LEFT JOIN {OLTP}.Projects p ON a.project_id = p.project_id "
        f"WHERE e.employee_id IS NULL OR p.project_id IS NULL",
    "orphan reviews / reviewers":
        f"SELECT COUNT(*), 0 FROM {OLTP}.Performance_Reviews r "
        f"LEFT JOIN {OLTP}.Employees e ON r.employee_id = e.employee_id "
        f"LEFT JOIN {OLTP}.Employees v ON r.reviewer_id = v.employee_id "
        f"WHERE e.employee_id IS NULL OR (r.reviewer_id IS NOT NULL AND v.employee_id IS NULL)",
    "orphan projects (department)":
        f"SELECT COUNT(*), 0 FROM {OLTP}.Projects p LEFT JOIN {OLTP}.Departments d "
        f"ON p.department_id = d.department_id WHERE d.department_id IS NULL",
}


def main() -> bool:
    load_dotenv()
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_OLTP", OLTP),
    )
    cur = conn.cursor()

    print("Running sp_load_oltp_from_staging() ...")
    t0 = time.time()
    try:
        cur.execute("CALL sp_load_oltp_from_staging()")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"ETL FAILED: {err}")
        return False
    print(f"Loaded in {time.time() - t0:.1f}s\n")

    ok = True
    print(f"{'check':42s} {'actual':>10s} {'expected':>10s}")
    for label, sql in CHECKS.items():
        cur.execute(sql)
        actual, expected = cur.fetchone()
        passed = actual == expected
        ok &= passed
        print(f"{'PASS' if passed else 'FAIL'}  {label:36s} {actual:>10,} {expected:>10,}")

    cur.close()
    conn.close()
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)