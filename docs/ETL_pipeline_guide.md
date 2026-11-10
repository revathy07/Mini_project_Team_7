# Employee Analytics ETL pipeline

This guide describes how to initialize the MySQL schemas and load the
provided/generated CSV data through staging, OLTP, and the data warehouse.
Use MySQL Workbench or another MySQL client to execute the SQL files. Run
Python commands from the repository root with the project environment
installed (`uv sync`).

## Important: database initialization is destructive

The schema scripts below use `DROP DATABASE IF EXISTS` before recreating their
database. Running them deletes the existing contents of that database. Back
up any data you need and verify the target server and `.env` settings before
running them. Do not execute the DDL against a database you need to preserve.

The application IAM bootstrap is separate: it creates `app_users` in the OLTP
database with `CREATE TABLE IF NOT EXISTS` and does not recreate a database.
See the [project guide](./README.md#iam-and-access).

## SQL file map

- `sql/staging/01_staging_ddl.sql` — recreates `employee_staging` and its
  landing tables.
- `sql/oltp/01_oltp_ddl.sql` — recreates `employee_oltp` and its normalized
  operational tables.
- `sql/olap/02_olap_ddl.sql` — recreates `employee_dw` and its dimensions and
  fact tables.
- `sql/oltp/02_load_from_staging.sql` — creates
  `sp_load_oltp_from_staging()`.
- `sql/etl/03_etl_procedure.sql` — creates the warehouse dimension and fact
  load procedures other than employee history.
- `sql/etl/05_dim_employee.sql` — creates the employee SCD Type 2 history
  load procedures.
- `sql/etl/04_run_etl.sql` — optional SQL script to execute a full warehouse
  load after the schema and procedures exist.

## First-time database setup

Connect to the intended MySQL server and execute these scripts in order:

1. `sql/staging/01_staging_ddl.sql`
2. `sql/oltp/01_oltp_ddl.sql`
3. `sql/olap/02_olap_ddl.sql`
4. `sql/oltp/02_load_from_staging.sql`
5. `sql/etl/03_etl_procedure.sql`
6. `sql/etl/05_dim_employee.sql`

Set `.env` to point to those databases. The default names are
`employee_staging`, `employee_oltp`, and `employee_dw`; the database names can
be overridden with `DB_STAGING`, `DB_OLTP`, and `DB_DW`.

## Load and transform data

The processed CSVs are already available under `data/processed/`. To rebuild
them from the synthesizer, run:

```bash
uv run python -m src.synthesizer.pipeline
```

The default synthesis target is 100,000 employees and 1,500 projects. To
choose different counts:

```bash
uv run python -m src.synthesizer.pipeline --employees 100000 --projects 1500
```

Load staging, populate OLTP, then build the warehouse:

```bash
uv run python src/etls/load_staging.py
uv run python src/etls/run_oltp_load.py
uv run python src/etls/run_dw_etl.py
```

Each loader reports row counts and reconciliation checks. Stop and investigate
any failed check before proceeding to the next stage.

## Data flow

1. `load_staging.py` loads CSV files from `data/processed/` into staging
   tables.
2. `run_oltp_load.py` calls `sp_load_oltp_from_staging()` and verifies OLTP
   counts and referential-integrity checks.
3. `run_dw_etl.py` loads warehouse dimensions and facts, including the
   employee-history dimension, and runs reconciliation checks.

The `Dim_Employee` SCD Type 2 procedure uses half-open date ranges
`[start_date, end_date)`. The full history load rebuilds that dimension, so
warehouse fact tables must be loaded afterward; the ETL order does this.

## Verify the warehouse

After a successful run, use MySQL Workbench to check representative row counts:

```sql
SELECT COUNT(*) FROM employee_dw.Dim_Employee;
SELECT COUNT(*) FROM employee_dw.Dim_Department;
SELECT COUNT(*) FROM employee_dw.Fact_PerformanceReviews;
SELECT COUNT(*) FROM employee_dw.Fact_ProjectAllocations;
```

The counts depend on the input data and synthesis options. The Python ETL
scripts compare actual table counts with their source counts and print
pass/fail checks.
