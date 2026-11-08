-- 02_load_from_staging.sql: staging -> OLTP (idempotent: truncate and reload)
USE employee_oltp;

DELIMITER $$

DROP PROCEDURE IF EXISTS sp_load_oltp_from_staging$$
CREATE PROCEDURE sp_load_oltp_from_staging()
BEGIN
    -- If anything fails, switch FK checks back on before re-raising the error
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET FOREIGN_KEY_CHECKS = 1;
        RESIGNAL;
    END;

    -- Off while loading: Employees references itself (manager_id), and
    -- Departments.manager_id points back at Employees.
    -- Integrity is verified afterwards by the reconciliation script.
    SET FOREIGN_KEY_CHECKS = 0;

    TRUNCATE TABLE Employee_Change_Log;
    TRUNCATE TABLE Performance_Reviews;
    TRUNCATE TABLE Project_Assignments;
    TRUNCATE TABLE Projects;
    TRUNCATE TABLE Employees;
    TRUNCATE TABLE Departments;

    -- 1. Departments
    INSERT INTO Departments (department_id, department_code, department_name, location, budget)
    SELECT department_id,
           CONCAT('DEPT-', LPAD(department_id, 3, '0')),
           department_name, location, annual_budget
    FROM employee_staging.stg_departments;

    -- 2. Employees
    INSERT INTO Employees (
        employee_id, employee_code, first_name, last_name, email, gender, age,
        hire_date, termination_date, department_id, job_role, job_level,
        monthly_income, percent_salary_hike, manager_id, attrition, status,
        overtime, business_travel, distance_from_home, job_satisfaction,
        environment_satisfaction, work_life_balance, job_involvement,
        total_working_years)
    SELECT employee_id,
           CONCAT('EMP-', LPAD(employee_id, 6, '0')),
           first_name, last_name, email, gender, age,
           hire_date, termination_date, department_id, job_role, job_level,
           monthly_income, percent_salary_hike, manager_id, attrition,
           CASE WHEN termination_date IS NULL THEN 'Active' ELSE 'Terminated' END,
           overtime, business_travel, distance_from_home, job_satisfaction,
           environment_satisfaction, work_life_balance, job_involvement,
           total_working_years
    FROM employee_staging.stg_employees;

    -- 3. Department head = most senior active employee (ROW_NUMBER picks one per department)
    UPDATE Departments d
    JOIN (
        SELECT department_id, employee_id
        FROM (
            SELECT employee_id, department_id,
                   ROW_NUMBER() OVER (PARTITION BY department_id
                                      ORDER BY job_level DESC, hire_date ASC, employee_id) AS rn
            FROM Employees
            WHERE termination_date IS NULL
        ) ranked
        WHERE rn = 1
    ) head ON head.department_id = d.department_id
    SET d.manager_id = head.employee_id;

    -- 4. Projects (project_manager_id stays NULL: the source data has no such field)
    INSERT INTO Projects (
        project_id, project_code, project_name, department_id,
        start_date, planned_end_date, end_date, budget, status, priority)
    SELECT project_id,
           CONCAT('PROJ-', LPAD(project_id, 5, '0')),
           project_name, department_id,
           start_date, planned_end_date, end_date, budget, status, priority
    FROM employee_staging.stg_projects;

    -- 5. Assignments: released => Completed, still open => Active
    INSERT INTO Project_Assignments (
        assignment_id, employee_id, project_id, role_in_project,
        allocation_percentage, start_date, end_date, status)
    SELECT assignment_id, employee_id, project_id, role,
           allocation_pct, assigned_date, released_date,
           CASE WHEN released_date IS NULL THEN 'Active' ELSE 'Completed' END
    FROM employee_staging.stg_project_assignments;

    -- 6. Reviews: every real measure, no deduplication
    INSERT INTO Performance_Reviews (
        review_id, employee_id, reviewer_id, review_date, review_period,
        performance_score, performance_rating, goal_achievement_pct,
        peer_feedback_score, promotion_recommended)
    SELECT review_id, employee_id, reviewer_id, review_date, review_cycle,
           performance_score, performance_rating, goal_achievement_pct,
           peer_feedback_score, promotion_recommended
    FROM employee_staging.stg_performance_reviews;

    -- 7. Change log: compare each version with the previous one (LAG),
    --    then emit one row for every field that actually changed
    INSERT INTO Employee_Change_Log
        (employee_id, change_date, change_type, field_name, old_value, new_value)
    WITH hist AS (
        SELECT c.employee_id, c.version_no, c.change_type,
               c.effective_start_date                        AS change_date,
               d.department_name                             AS dept,
               c.job_role, c.job_level, c.monthly_income,
               LAG(d.department_name) OVER w                 AS prev_dept,
               LAG(c.job_role)        OVER w                 AS prev_role,
               LAG(c.job_level)       OVER w                 AS prev_level,
               LAG(c.monthly_income)  OVER w                 AS prev_income
        FROM employee_staging.stg_employee_changes c
        JOIN employee_staging.stg_departments d ON d.department_id = c.department_id
        WINDOW w AS (PARTITION BY c.employee_id ORDER BY c.version_no)
    )
    SELECT employee_id, change_date, change_type, 'department', prev_dept, dept
      FROM hist WHERE version_no > 1 AND dept <> prev_dept
    UNION ALL
    SELECT employee_id, change_date, change_type, 'job_role', prev_role, job_role
      FROM hist WHERE version_no > 1 AND job_role <> prev_role
    UNION ALL
    SELECT employee_id, change_date, change_type, 'job_level',
           CAST(prev_level AS CHAR), CAST(job_level AS CHAR)
      FROM hist WHERE version_no > 1 AND job_level <> prev_level
    UNION ALL
    SELECT employee_id, change_date, change_type, 'monthly_income',
           CAST(prev_income AS CHAR), CAST(monthly_income AS CHAR)
      FROM hist WHERE version_no > 1 AND monthly_income <> prev_income;

    SET FOREIGN_KEY_CHECKS = 1;
END$$

DELIMITER ;