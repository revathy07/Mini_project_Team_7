-- 04_run_etl.sql
-- Executes the ETL pipeline to populate the Data Warehouse
-- IMPORTANT: Dimensions MUST be loaded before Facts to satisfy Foreign Keys.


-- 1. Load Dimensions First
CALL employee_dw.sp_load_dim_date();
CALL employee_dw.sp_load_dim_department();
CALL employee_dw.sp_load_dim_project();

-- Note: sp_load_dim_employee_scd2() is skipped here because the Python bulk loader 
-- (load_data.py) handles the initial 160,000+ SCD2 history rows directly from the CSVs.

-- 2. Load Fact Tables Second
CALL employee_dw.sp_load_fact_performance();
CALL employee_dw.sp_load_fact_project_allocations();