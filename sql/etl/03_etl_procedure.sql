-- 03_etl_procedure.sql: dimension loads (except Dim_Employee) and fact loads
USE employee_dw;

DELIMITER $$

-- 1. Dim_Department
DROP PROCEDURE IF EXISTS sp_load_dim_department$$
CREATE PROCEDURE sp_load_dim_department()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN SET FOREIGN_KEY_CHECKS = 1; RESIGNAL; END;

    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE Dim_Department;
    INSERT INTO Dim_Department (department_code, department_name, location, budget)
    SELECT department_code, department_name, location, budget
    FROM employee_oltp.Departments;
    SET FOREIGN_KEY_CHECKS = 1;
END$$

-- 2. Dim_Date (2010-01-01 .. 2030-12-31)
DROP PROCEDURE IF EXISTS sp_load_dim_date$$
CREATE PROCEDURE sp_load_dim_date()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN SET FOREIGN_KEY_CHECKS = 1; RESIGNAL; END;

    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE Dim_Date;
    SET SESSION cte_max_recursion_depth = 10000;

    INSERT INTO Dim_Date (date_key, full_date, day_of_week, month_name, quarter, year)
    WITH RECURSIVE date_series AS (
        SELECT CAST('2010-01-01' AS DATE) AS dt
        UNION ALL
        SELECT DATE_ADD(dt, INTERVAL 1 DAY) FROM date_series WHERE dt < CAST('2030-12-31' AS DATE)
    )
    SELECT CAST(DATE_FORMAT(dt, '%Y%m%d') AS UNSIGNED), dt,
           DAYNAME(dt), MONTHNAME(dt), QUARTER(dt), YEAR(dt)
    FROM date_series;
    SET FOREIGN_KEY_CHECKS = 1;
END$$

-- 3. Dim_Project (now with timeline and budget, for bottleneck analysis)
DROP PROCEDURE IF EXISTS sp_load_dim_project$$
CREATE PROCEDURE sp_load_dim_project()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN SET FOREIGN_KEY_CHECKS = 1; RESIGNAL; END;

    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE Dim_Project;
    INSERT INTO Dim_Project (project_code, project_name, department_name, status,
                             priority, start_date, planned_end_date, end_date, budget)
    SELECT p.project_code, p.project_name, d.department_name, p.status,
           p.priority, p.start_date, p.planned_end_date, p.end_date, p.budget
    FROM employee_oltp.Projects p
    LEFT JOIN employee_oltp.Departments d ON d.department_id = p.department_id;
    SET FOREIGN_KEY_CHECKS = 1;
END$$

-- 4. Fact_PerformanceReviews
--    employee_sk / department_sk = the employee VERSION valid on the review date
DROP PROCEDURE IF EXISTS sp_load_fact_performance$$
CREATE PROCEDURE sp_load_fact_performance()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN SET FOREIGN_KEY_CHECKS = 1; RESIGNAL; END;

    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE Fact_PerformanceReviews;

    INSERT INTO Fact_PerformanceReviews (
        employee_sk, department_sk, date_key, reviewer_employee_sk, review_period,
        performance_score, performance_rating, goal_achievement_pct,
        peer_feedback_score, promotion_recommended)
    WITH rev AS (
        SELECT pr.review_date, pr.review_period, pr.performance_score,
               pr.performance_rating, pr.goal_achievement_pct,
               pr.peer_feedback_score, pr.promotion_recommended,
               e.employee_code, rv.employee_code AS reviewer_code
        FROM employee_oltp.Performance_Reviews pr
        JOIN employee_oltp.Employees e  ON e.employee_id  = pr.employee_id
        LEFT JOIN employee_oltp.Employees rv ON rv.employee_id = pr.reviewer_id
    )
    SELECT de.employee_sk,
           dd.department_sk,
           CAST(DATE_FORMAT(r.review_date, '%Y%m%d') AS UNSIGNED),
           dr.employee_sk,
           r.review_period, r.performance_score, r.performance_rating,
           r.goal_achievement_pct, r.peer_feedback_score, r.promotion_recommended
    FROM rev r
    JOIN Dim_Employee de ON de.employee_code = r.employee_code
                        AND r.review_date >= de.start_date AND r.review_date < de.end_date
    JOIN Dim_Department dd ON dd.department_name = de.department_name
    LEFT JOIN Dim_Employee dr ON dr.employee_code = r.reviewer_code
                             AND r.review_date >= dr.start_date AND r.review_date < dr.end_date;

    SET FOREIGN_KEY_CHECKS = 1;
END$$

-- 5. Fact_ProjectAllocations: employee version valid on the assignment start date
DROP PROCEDURE IF EXISTS sp_load_fact_project_allocations$$
CREATE PROCEDURE sp_load_fact_project_allocations()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN SET FOREIGN_KEY_CHECKS = 1; RESIGNAL; END;

    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE Fact_ProjectAllocations;

    INSERT INTO Fact_ProjectAllocations (
        employee_sk, project_sk, date_key, role_in_project, allocation_percentage)
    SELECT de.employee_sk, dp.project_sk,
           CAST(DATE_FORMAT(pa.start_date, '%Y%m%d') AS UNSIGNED),
           pa.role_in_project, pa.allocation_percentage
    FROM employee_oltp.Project_Assignments pa
    JOIN employee_oltp.Employees e ON e.employee_id = pa.employee_id
    JOIN employee_oltp.Projects  p ON p.project_id  = pa.project_id
    JOIN Dim_Employee de ON de.employee_code = e.employee_code
                        AND pa.start_date >= de.start_date AND pa.start_date < de.end_date
    JOIN Dim_Project dp ON dp.project_code = p.project_code;

    SET FOREIGN_KEY_CHECKS = 1;
END$$

DELIMITER ;