-- 03_etl_procedure.sql (ETL & SCD Type 2)

USE employee_oltp;

DELIMITER $$

-- 1. Load Dim_Department
DROP PROCEDURE IF EXISTS sp_load_dim_department$$
CREATE PROCEDURE sp_load_dim_department()
BEGIN
    TRUNCATE TABLE employee_dw.Dim_Department;
    INSERT INTO employee_dw.Dim_Department (department_code, department_name, location, budget)
    SELECT department_code, department_name, location, budget FROM employee_oltp.Departments;
END$$

-- 2. Load Dim_Date
DROP PROCEDURE IF EXISTS sp_load_dim_date$$
CREATE PROCEDURE sp_load_dim_date()
BEGIN
    TRUNCATE TABLE employee_dw.Dim_Date;
    SET @@cte_max_recursion_depth = 10000; 
    
    INSERT INTO employee_dw.Dim_Date (date_key, full_date, day_of_week, month_name, quarter, year)
    WITH RECURSIVE date_series AS (
        SELECT '2010-01-01' AS dt
        UNION ALL
        SELECT DATE_ADD(dt, INTERVAL 1 DAY) FROM date_series WHERE dt < '2030-12-31'
    )
    SELECT 
        CAST(DATE_FORMAT(dt, '%Y%m%d') AS UNSIGNED) AS date_key,
        dt AS full_date,
        DAYNAME(dt) AS day_of_week,
        MONTHNAME(dt) AS month_name,
        QUARTER(dt) AS quarter,
        YEAR(dt) AS year
    FROM date_series;
END$$

-- 3. Load Dim_Project
DROP PROCEDURE IF EXISTS sp_load_dim_project$$
CREATE PROCEDURE sp_load_dim_project()
BEGIN
    TRUNCATE TABLE employee_dw.Dim_Project;
    INSERT INTO employee_dw.Dim_Project (project_code, project_name, department_name, status)
    SELECT 
        p.project_code, p.project_name, d.department_name, p.status
    FROM employee_oltp.Projects p
    LEFT JOIN employee_oltp.Departments d ON p.department_id = d.department_id;
END$$

-- 4. Load Dim_Employee (SCD Type 2)
DROP PROCEDURE IF EXISTS sp_load_dim_employee_scd2$$
CREATE PROCEDURE sp_load_dim_employee_scd2()
BEGIN
    -- Step A: Close current records for changed employees
    UPDATE employee_dw.Dim_Employee d
    JOIN employee_oltp.Employees e ON d.employee_code = e.employee_code
    JOIN employee_oltp.Departments dept ON e.department_id = dept.department_id
    SET d.end_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY),
        d.is_current = FALSE
    WHERE d.is_current = TRUE
      AND (d.department_name <> dept.department_name OR d.job_role <> e.job_role 
           OR d.job_level <> e.job_level OR d.monthly_income <> e.monthly_income);

    -- Step B: Insert new versions or brand new employees
    INSERT INTO employee_dw.Dim_Employee (
        employee_code, full_name, email, department_name, 
        job_role, job_level, monthly_income, hire_date, 
        attrition_flag, start_date, end_date, is_current
    )
    SELECT 
        e.employee_code, CONCAT(e.first_name, ' ', e.last_name), e.email, dept.department_name, 
        e.job_role, e.job_level, e.monthly_income, e.hire_date, e.attrition,
        CURDATE(), '9999-12-31', TRUE
    FROM employee_oltp.Employees e
    JOIN employee_oltp.Departments dept ON e.department_id = dept.department_id
    LEFT JOIN employee_dw.Dim_Employee dim ON e.employee_code = dim.employee_code AND dim.is_current = TRUE
    WHERE dim.employee_sk IS NULL;
END$$

-- 5. Load Fact_PerformanceReviews
DROP PROCEDURE IF EXISTS sp_load_fact_performance$$
CREATE PROCEDURE sp_load_fact_performance()
BEGIN
    TRUNCATE TABLE employee_dw.Fact_PerformanceReviews;
    INSERT INTO employee_dw.Fact_PerformanceReviews (
        employee_sk, department_sk, date_key, reviewer_employee_sk,
        review_period, performance_rating, job_satisfaction, work_life_balance, percent_salary_hike
    )
    SELECT 
        dim_e.employee_sk, dim_d.department_sk, CAST(DATE_FORMAT(pr.review_date, '%Y%m%d') AS UNSIGNED),
        dim_r.employee_sk, pr.review_period, pr.performance_rating, pr.job_satisfaction, 
        pr.work_life_balance, pr.percent_salary_hike
    FROM employee_oltp.Performance_Reviews pr
    JOIN employee_oltp.Employees e ON pr.employee_id = e.employee_id
    JOIN employee_oltp.Departments d ON e.department_id = d.department_id
    JOIN employee_dw.Dim_Employee dim_e ON e.employee_code = dim_e.employee_code 
      AND pr.review_date >= dim_e.start_date AND pr.review_date < dim_e.end_date
    JOIN employee_dw.Dim_Department dim_d ON d.department_code = dim_d.department_code
    LEFT JOIN employee_oltp.Employees rev ON pr.reviewer_id = rev.employee_id
    LEFT JOIN employee_dw.Dim_Employee dim_r ON rev.employee_code = dim_r.employee_code 
      AND pr.review_date >= dim_r.start_date AND pr.review_date < dim_r.end_date;
END$$

-- 6. Load Fact_ProjectAllocations
DROP PROCEDURE IF EXISTS sp_load_fact_project_allocations$$
CREATE PROCEDURE sp_load_fact_project_allocations()
BEGIN
    TRUNCATE TABLE employee_dw.Fact_ProjectAllocations;
    INSERT INTO employee_dw.Fact_ProjectAllocations (
        employee_sk, project_sk, date_key, role_in_project, allocation_percentage
    )
    SELECT 
        de.employee_sk, dp.project_sk, CAST(DATE_FORMAT(pa.start_date, '%Y%m%d') AS UNSIGNED), 
        pa.role_in_project, pa.allocation_percentage
    FROM employee_oltp.Project_Assignments pa
    JOIN employee_oltp.Employees e ON pa.employee_id = e.employee_id
    JOIN employee_oltp.Projects p ON pa.project_id = p.project_id
    JOIN employee_dw.Dim_Employee de ON e.employee_code = de.employee_code AND de.is_current = TRUE
    JOIN employee_dw.Dim_Project dp ON p.project_code = dp.project_code;
END$$

DELIMITER ;