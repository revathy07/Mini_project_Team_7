-- 05_dim_employee.sql: Dim_Employee SCD Type 2 (window convention [start_date, end_date))
USE employee_dw;

DELIMITER $$

-- ---------------------------------------------------------------
-- 1. One-time backfill: rebuild every version from the history
-- ---------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_dim_employee_history$$
CREATE PROCEDURE sp_load_dim_employee_history()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET FOREIGN_KEY_CHECKS = 1;
        RESIGNAL;
    END;

    -- Facts reference Dim_Employee, so they must be reloaded afterwards (6E)
    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE Dim_Employee;

    INSERT INTO Dim_Employee (
        employee_code, full_name, email, department_name, job_role, job_level,
        monthly_income, hire_date, attrition_flag, start_date, end_date, is_current)
    WITH versions AS (
        -- employees WITH history: LEAD() gives the next version's start = this version's end
        SELECT c.employee_id, c.department_id, c.job_role, c.job_level, c.monthly_income,
               c.effective_start_date                   AS start_date,
               LEAD(c.effective_start_date) OVER w      AS next_start
        FROM employee_staging.stg_employee_changes c
        WINDOW w AS (PARTITION BY c.employee_id ORDER BY c.version_no)
    ),
    all_versions AS (
        SELECT employee_id, department_id, job_role, job_level, monthly_income,
               start_date, next_start
        FROM versions
        UNION ALL
        -- employees WITHOUT history: a single open-ended version from the hire date
        SELECT e.employee_id, e.department_id, e.job_role, e.job_level, e.monthly_income,
               e.hire_date, NULL
        FROM employee_oltp.Employees e
        WHERE NOT EXISTS (SELECT 1 FROM employee_staging.stg_employee_changes c
                          WHERE c.employee_id = e.employee_id)
    )
    SELECT e.employee_code,
           CONCAT(e.first_name, ' ', e.last_name),
           e.email,
           d.department_name,
           v.job_role, v.job_level, v.monthly_income,
           e.hire_date,
           e.attrition,
           v.start_date,
           COALESCE(v.next_start, CAST('9999-12-31' AS DATE)),
           v.next_start IS NULL
    FROM all_versions v
    JOIN employee_oltp.Employees   e ON e.employee_id   = v.employee_id
    JOIN employee_oltp.Departments d ON d.department_id = v.department_id
    ORDER BY e.employee_code, v.start_date;

    SET FOREIGN_KEY_CHECKS = 1;
END$$

-- ---------------------------------------------------------------
-- 2. Incremental SCD2: compare OLTP current state with the current dimension row
-- ---------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_dim_employee_scd2$$
CREATE PROCEDURE sp_load_dim_employee_scd2(IN p_effective_date DATE)
BEGIN
    -- Step 1: close the current version of anyone whose tracked attributes changed.
    -- end_date = the date the new version starts (no gap, no overlap).
    UPDATE Dim_Employee d
    JOIN employee_oltp.Employees   e    ON e.employee_code  = d.employee_code
    JOIN employee_oltp.Departments dept ON dept.department_id = e.department_id
    SET d.end_date   = p_effective_date,
        d.is_current = FALSE
    WHERE d.is_current = TRUE
      AND ( NOT (d.department_name <=> dept.department_name)
         OR NOT (d.job_role        <=> e.job_role)
         OR NOT (d.job_level       <=> e.job_level)
         OR NOT (d.monthly_income  <=> e.monthly_income) );

    -- Step 2: open a new current version for anyone without one.
    -- That is both changed employees (just closed) and brand-new hires.
    INSERT INTO Dim_Employee (
        employee_code, full_name, email, department_name, job_role, job_level,
        monthly_income, hire_date, attrition_flag, start_date, end_date, is_current)
    SELECT e.employee_code,
           CONCAT(e.first_name, ' ', e.last_name),
           e.email, dept.department_name, e.job_role, e.job_level, e.monthly_income,
           e.hire_date, e.attrition,
           IF(seen.employee_code IS NULL, e.hire_date, p_effective_date),  -- new hire vs change
           CAST('9999-12-31' AS DATE),
           TRUE
    FROM employee_oltp.Employees e
    JOIN employee_oltp.Departments dept ON dept.department_id = e.department_id
    LEFT JOIN Dim_Employee cur
           ON cur.employee_code = e.employee_code AND cur.is_current = TRUE
    LEFT JOIN (SELECT DISTINCT employee_code FROM Dim_Employee) seen
           ON seen.employee_code = e.employee_code
    WHERE cur.employee_sk IS NULL;
END$$

DELIMITER ;