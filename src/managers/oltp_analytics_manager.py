from src.database.base_manager import BaseManager

# Quartile of pay WITHIN job level, over all employees (window function NTILE)
_ATTRITION_SQL = """
    WITH raw AS (
        SELECT e.department_id,
               e.attrition AS left_flag,
               e.overtime, e.business_travel, e.job_satisfaction,
               TIMESTAMPDIFF(YEAR, e.hire_date,
                             COALESCE(e.termination_date, CURDATE())) AS tenure_years,
               NTILE(4) OVER (PARTITION BY e.job_level
                              ORDER BY e.monthly_income) AS income_q
        FROM Employees e
    ),
    scoped AS (
        SELECT left_flag,
               CASE WHEN overtime = 1 THEN 'Yes' WHEN overtime = 0 THEN 'No' END AS overtime_b,
               business_travel AS travel_b,
               CASE WHEN job_satisfaction IS NULL THEN NULL
                    WHEN job_satisfaction <= 2 THEN 'Low (1-2)'
                    ELSE 'High (3-4)' END AS satisfaction_b,
               CASE WHEN tenure_years < 2  THEN '0-1 yrs'
                    WHEN tenure_years < 5  THEN '2-4 yrs'
                    WHEN tenure_years < 10 THEN '5-9 yrs'
                    ELSE '10+ yrs' END AS tenure_b,
               CONCAT('Q', income_q) AS income_b
        FROM raw
        WHERE (%s IS NULL OR department_id = %s)
    )
    SELECT 'Overtime' AS factor, overtime_b AS bucket,
           COUNT(*) AS headcount, SUM(left_flag) AS leavers
      FROM scoped WHERE overtime_b IS NOT NULL GROUP BY overtime_b
    UNION ALL
    SELECT 'Business travel', travel_b, COUNT(*), SUM(left_flag)
      FROM scoped WHERE travel_b IS NOT NULL GROUP BY travel_b
    UNION ALL
    SELECT 'Job satisfaction', satisfaction_b, COUNT(*), SUM(left_flag)
      FROM scoped WHERE satisfaction_b IS NOT NULL GROUP BY satisfaction_b
    UNION ALL
    SELECT 'Tenure', tenure_b, COUNT(*), SUM(left_flag)
      FROM scoped GROUP BY tenure_b
    UNION ALL
    SELECT 'Income quartile (within level)', income_b, COUNT(*), SUM(left_flag)
      FROM scoped GROUP BY income_b
"""

# Rule-based score 0-7 for ACTIVE employees. One point per risk factor.
_RISK_CTE = """
    WITH raw AS (
        SELECT e.employee_id, e.employee_code,
               CONCAT(e.first_name, ' ', e.last_name) AS full_name,
               e.department_id, e.job_role, e.hire_date, e.termination_date,
               e.overtime, e.job_satisfaction, e.work_life_balance,
               e.business_travel, e.distance_from_home,
               NTILE(4) OVER (PARTITION BY e.job_level
                              ORDER BY e.monthly_income) AS income_q
        FROM Employees e
    ),
    flags AS (
        SELECT raw.*, d.department_name,
               COALESCE(overtime = 1, 0)                           AS f_overtime,
               COALESCE(job_satisfaction <= 2, 0)                  AS f_satisfaction,
               COALESCE(work_life_balance <= 2, 0)                 AS f_balance,
               COALESCE(business_travel = 'Travel_Frequently', 0)  AS f_travel,
               COALESCE(distance_from_home > 20, 0)                AS f_distance,
               (income_q = 1)                                      AS f_income,
               (TIMESTAMPDIFF(YEAR, hire_date, CURDATE()) < 2)     AS f_new
        FROM raw
        JOIN Departments d ON d.department_id = raw.department_id
        WHERE raw.termination_date IS NULL
          AND (%s IS NULL OR raw.department_id = %s)
    ),
    scored AS (
        SELECT flags.*,
               (f_overtime + f_satisfaction + f_balance + f_travel
                + f_distance + f_income + f_new) AS risk_score
        FROM flags
    )
"""


class OltpAnalyticsManager(BaseManager):
    """Read-only analytics on operational data (attrition drivers, allocation).
    These attributes are not in the warehouse, so they are read from OLTP."""

    database_kind = "oltp"

    def get_attrition_by_factor(self, department_id=None):
        return self.fetch_all(_ATTRITION_SQL, (department_id, department_id))

    def get_risk_distribution(self, department_id=None):
        sql = _RISK_CTE + """
            SELECT risk_score, COUNT(*) AS employees
            FROM scored GROUP BY risk_score ORDER BY risk_score
        """
        return self.fetch_all(sql, (department_id, department_id))

    def get_high_risk_employees(self, department_id=None, limit=25):
        sql = _RISK_CTE + """
            SELECT employee_code, full_name, department_name, job_role, risk_score,
                   CONCAT_WS(', ',
                       IF(f_overtime,     'overtime', NULL),
                       IF(f_satisfaction, 'low job satisfaction', NULL),
                       IF(f_balance,      'poor work-life balance', NULL),
                       IF(f_travel,       'frequent travel', NULL),
                       IF(f_distance,     'long commute', NULL),
                       IF(f_income,       'lowest pay quartile', NULL),
                       IF(f_new,          'under 2 years tenure', NULL)
                   ) AS risk_factors
            FROM scored
            ORDER BY risk_score DESC, hire_date DESC, employee_id
            LIMIT %s
        """
        return self.fetch_all(sql, (department_id, department_id, int(limit)))

    def get_allocation_bands(self, department_id=None):
        return self.fetch_all("""
            WITH alloc AS (
                SELECT e.employee_id,
                       COALESCE(SUM(pa.allocation_percentage), 0) AS total
                FROM Employees e
                LEFT JOIN Project_Assignments pa
                       ON pa.employee_id = e.employee_id AND pa.status = 'Active'
                WHERE e.termination_date IS NULL
                  AND (%s IS NULL OR e.department_id = %s)
                GROUP BY e.employee_id
            )
            SELECT CASE WHEN total = 0   THEN '0 (unassigned)'
                        WHEN total <= 50  THEN '1-50'
                        WHEN total <= 100 THEN '51-100'
                        WHEN total <= 150 THEN '101-150'
                        ELSE '151+' END AS band,
                   COUNT(*) AS employees
            FROM alloc
            GROUP BY band
        """, (department_id, department_id))

    def get_overallocated_employees(self, department_id=None, limit=25):
        return self.fetch_all("""
            SELECT e.employee_code,
                   CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                   d.department_name,
                   COUNT(*) AS open_assignments,
                   SUM(pa.allocation_percentage) AS total_allocation,
                   COUNT(*) OVER () AS total_overallocated
            FROM Project_Assignments pa
            JOIN Employees e   ON e.employee_id = pa.employee_id
            JOIN Departments d ON d.department_id = e.department_id
            WHERE pa.status = 'Active'
              AND e.termination_date IS NULL
              AND (%s IS NULL OR e.department_id = %s)
            GROUP BY e.employee_id, e.employee_code, e.first_name,
                     e.last_name, d.department_name
            HAVING SUM(pa.allocation_percentage) > 100
            ORDER BY total_allocation DESC, open_assignments DESC
            LIMIT %s
        """, (department_id, department_id, int(limit)))