# SQL scripts

Run in this order (each `*_ddl.sql` drops and recreates its database and any stored procedures in it).

| Order | File | Creates |
|---|---|---|
| 1 | `staging/01_staging_ddl.sql` | `employee_staging`: raw landing tables, no foreign keys |
| 2 | `oltp/01_oltp_ddl.sql` | `employee_oltp`: normalized operational tables |
| 3 | `oltp/02_load_from_staging.sql` | `sp_load_oltp_from_staging` (CTE + `LAG()` builds the change log) |
| 4 | `olap/02_olap_ddl.sql` | `employee_dw`: star schema with surrogate keys |
| 5 | `etl/03_etl_procedure.sql` | Dimension and fact load procedures (full and incremental) |
| 6 | `etl/05_dim_employee.sql` | `Dim_Employee` SCD2: history backfill (CTE + `LEAD()`) and incremental update |

`etl/04_run_etl.sql` documents the call order only; use the Python runners instead.

Re-running a DDL file wipes that database, including its procedures. Re-run the procedure files after it.