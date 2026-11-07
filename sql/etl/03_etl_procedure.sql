-- 03_etl_procedure.sql (ETL & SCD Type 2)

USE employee_oltp;

DELIMITER $$


-- 1. Load Dim_Department (Simple Overwrite / SCD Type 1)

CREATE PROCEDURE sp_load_dim_department()
BEGIN
    TRUNCATE TABLE employee_dw.Dim_Department;
    
    INSERT INTO employee_dw.Dim_Department (department_code, department_name, location, budget)
    SELECT department_code, department_name, location, budget
    FROM Departments;
END$$

-- 2. Load Dim_Employee (SCD Type 2)

CREATE PROCEDURE sp_load_dim_employee_scd2()
BEGIN
    -- Step A: Close current records for employees whose attributes changed in OLTP
    UPDATE employee_dw.Dim_Employee d
    JOIN Employees e ON d.employee_code = e.employee_code
    JOIN Departments dept ON e.department_id = dept.department_id
    SET d.end_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY),
        d.is_current = FALSE
    WHERE d.is_current = TRUE
      AND (
          d.department_name <> dept.department_name OR
          d.job_role <> e.job_role OR
          d.job_level <> e.job_level OR
          d.monthly_income <> e.monthly_income
      );

    -- Step B: Insert new versions for changed employees OR brand new employees
    INSERT INTO employee_dw.Dim_Employee (
        employee_code, full_name, email, department_name, 
        job_role, job_level, monthly_income, hire_date, 
        attrition_flag, start_date, end_date, is_current
    )
    SELECT 
        e.employee_code, 
        CONCAT(e.first_name, ' ', e.last_name),
        e.email, 
        dept.department_name, 
        e.job_role, 
        e.job_level, 
        e.monthly_income, 
        e.hire_date, 
        e.attrition,
        CURDATE() AS start_date,
        '9999-12-31' AS end_date,
        TRUE AS is_current
    FROM Employees e
    JOIN Departments dept ON e.department_id = dept.department_id
    LEFT JOIN employee_dw.Dim_Employee dim 
           ON e.employee_code = dim.employee_code AND dim.is_current = TRUE
    WHERE dim.employee_sk IS NULL; -- Only inserts if they are new or were just closed in Step A
END$$


-- 3. Load Fact_PerformanceReviews

CREATE PROCEDURE sp_load_fact_performance()
BEGIN
    TRUNCATE TABLE employee_dw.Fact_PerformanceReviews;
    
    INSERT INTO employee_dw.Fact_PerformanceReviews (
        employee_sk, department_sk, date_key, reviewer_employee_sk,
        review_period, performance_rating, job_satisfaction, work_life_balance, percent_salary_hike
    )
    SELECT 
        dim_e.employee_sk,
        dim_d.department_sk,
        CAST(DATE_FORMAT(pr.review_date, '%Y%m%d') AS UNSIGNED) AS date_key,
        dim_r.employee_sk AS reviewer_employee_sk,
        pr.review_period,
        pr.performance_rating,
        pr.job_satisfaction,
        pr.work_life_balance,
        pr.percent_salary_hike
    FROM Performance_Reviews pr
    -- Join to get employee surrogate key (SCD2: match the version active on review date)
    JOIN employee_dw.Dim_Employee dim_e 
      ON pr.employee_id = (SELECT employee_id FROM Employees WHERE employee_code = dim_e.employee_code)
     AND pr.review_date >= dim_e.start_date 
     AND pr.review_date < dim_e.end_date
    -- Join to get department surrogate key
    JOIN Departments d ON (SELECT department_id FROM Employees WHERE employee_id = pr.employee_id) = d.department_id
    JOIN employee_dw.Dim_Department dim_d ON d.department_code = dim_d.department_code
    -- Join to get reviewer surrogate key
    LEFT JOIN employee_dw.Dim_Employee dim_r 
      ON pr.reviewer_id = (SELECT employee_id FROM Employees WHERE employee_code = dim_r.employee_code)
     AND pr.review_date >= dim_r.start_date 
     AND pr.review_date < dim_r.end_date;
END$$

DELIMITER ;