import os
import sys
import time

import mysql.connector
from dotenv import load_dotenv

OLTP = "employee_oltp"

# Dimensions first, facts last. The first failure stops the run.
PROCEDURES = [
    "sp_load_dim_date",
    "sp_load_dim_department",
    "sp_load_dim_project",
    "sp_load_dim_employee_history",
    "sp_load_fact_performance",
    "sp_load_fact_project_allocations",
]

# (actual, expected) must be equal
CHECKS = {
    "Dim_Date covers every day 2010-2030":
        "SELECT (SELECT COUNT(*) FROM Dim_Date), DATEDIFF('2030-12-31','2010-01-01') + 1",
    "Dim_Department rows = OLTP":
        f"SELECT (SELECT COUNT(*) FROM Dim_Department), (SELECT COUNT(*) FROM {OLTP}.Departments)",
    "Dim_Project rows = OLTP":
        f"SELECT (SELECT COUNT(*) FROM Dim_Project), (SELECT COUNT(*) FROM {OLTP}.Projects)",
    "Fact_PerformanceReviews rows = OLTP reviews":
        f"SELECT (SELECT COUNT(*) FROM Fact_PerformanceReviews), "
        f"(SELECT COUNT(*) FROM {OLTP}.Performance_Reviews)",
    "Fact_ProjectAllocations rows = OLTP assignments":
        f"SELECT (SELECT COUNT(*) FROM Fact_ProjectAllocations), "
        f"(SELECT COUNT(*) FROM {OLTP}.Project_Assignments)",
    "review dept = dept of the employee version":
        "SELECT COUNT(*), 0 FROM Fact_PerformanceReviews f "
        "JOIN Dim_Employee de ON de.employee_sk = f.employee_sk "
        "JOIN Dim_Department dd ON dd.department_sk = f.department_sk "
        "WHERE dd.department_name <> de.department_name",
    "review date falls inside its employee version":
        "SELECT COUNT(*), 0 FROM Fact_PerformanceReviews f "
        "JOIN Dim_Employee de ON de.employee_sk = f.employee_sk "
        "JOIN Dim_Date dt ON dt.date_key = f.date_key "
        "WHERE dt.full_date < de.start_date OR dt.full_date >= de.end_date",
    "allocation date falls inside its employee version":
        "SELECT COUNT(*), 0 FROM Fact_ProjectAllocations f "
        "JOIN Dim_Employee de ON de.employee_sk = f.employee_sk "
        "JOIN Dim_Date dt ON dt.date_key = f.date_key "
        "WHERE dt.full_date < de.start_date OR dt.full_date >= de.end_date",
}

# Informational: printed, not pass/fail
INFO = {
    "reviews attributed to a former department":
        "SELECT COUNT(*) FROM Fact_PerformanceReviews f "
        "JOIN Dim_Employee de  ON de.employee_sk = f.employee_sk "
        "JOIN Dim_Employee cur ON cur.employee_code = de.employee_code AND cur.is_current = 1 "
        "WHERE de.department_name <> cur.department_name",
    "reviews with a reviewer in OLTP but none on the review date":
        f"SELECT (SELECT COUNT(*) FROM {OLTP}.Performance_Reviews WHERE reviewer_id IS NOT NULL) "
        f"- (SELECT COUNT(*) FROM Fact_PerformanceReviews WHERE reviewer_employee_sk IS NOT NULL)",
}

# Simpler and faster: total reviews with reviewer vs facts with reviewer
INFO["reviews with a reviewer in OLTP but none on the review date"] = (
    f"SELECT (SELECT COUNT(*) FROM {OLTP}.Performance_Reviews WHERE reviewer_id IS NOT NULL) "
    f"- (SELECT COUNT(*) FROM Fact_PerformanceReviews WHERE reviewer_employee_sk IS NOT NULL)"
)


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

    for proc in PROCEDURES:
        t0 = time.time()
        print(f"Executing {proc}() ...", end=" ", flush=True)
        try:
            cur.execute(f"CALL {proc}()")
            conn.commit()
        except mysql.connector.Error as err:
            print(f"FAILED\n  {err}\nStopping: later steps depend on this one.")
            return False
        print(f"done in {time.time() - t0:.1f}s")

    ok = True
    print(f"\n{'check':52s} {'actual':>10s} {'expected':>10s}")
    for label, sql in CHECKS.items():
        cur.execute(sql)
        actual, expected = cur.fetchone()
        passed = actual == expected
        ok &= passed
        print(f"{'PASS' if passed else 'FAIL'}  {label:46s} {actual:>10,} {expected:>10,}")

    print("\nInformational:")
    for label, sql in INFO.items():
        cur.execute(sql)
        print(f"  {label}: {cur.fetchone()[0]:,}")

    cur.close()
    conn.close()
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)