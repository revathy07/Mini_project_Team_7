-- 04_run_etl.sql: full warehouse rebuild. Dimensions first, then facts.
CALL employee_dw.sp_load_dim_date();
CALL employee_dw.sp_load_dim_department();
CALL employee_dw.sp_load_dim_project();
CALL employee_dw.sp_load_dim_employee_history();   -- rebuilds from staging history
CALL employee_dw.sp_load_fact_performance();
CALL employee_dw.sp_load_fact_project_allocations();