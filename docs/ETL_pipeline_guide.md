# Employee Analytics - ETL Pipeline Documentation

This document explains the architecture of the ETL pipeline, the purpose of each script, and the exact sequence of commands required to build and populate the Data Warehouse.

## File Explanations

### 1. Database Setup (SQL)
*   **`sql/staging/01_staging_ddl.sql`**: Creates the staging area. Raw CSVs are loaded here first to prevent corrupting the main database.
*   **`sql/oltp/02_oltp_ddl.sql`**: Creates the operational database (`employee_oltp`). This is a normalized (3NF) schema designed for the Streamlit app's daily transactions.
*   **`sql/warehouse/03_olap_ddl.sql`**: Creates the Data Warehouse (`employee_dw`). This is a Star Schema containing Fact tables and Dimension tables, with optimized indexes.
*   **`sql/procedures/04_etl_procedures.sql`**: Creates the Stored Procedures. These contain the "brains" of the ETL—handling SCD Type 2 for employee history, mapping surrogate keys, and formatting dates.

### 2. Data Loading & Orchestration (Python)
*   **`src/etls/load_staging.py`**: (If used) A helper script to bulk-load CSV data into the Staging tables.
*   **`src/etls/run_oltp_load.py`**: The bulk loader. It reads the synthetic CSVs, cleans the data, and pushes it into the Staging tables. It then triggers the SQL procedures to move data into the OLTP database.
*   **`src/etls/run_dw_etl.py`**: The Python orchestrator. It connects to MySQL, executes the ETL Stored Procedures, and performs **data reconciliation checks** (verifying row counts and SCD2 date ranges). Because it bypasses the Workbench GUI, it prevents 30-second timeout errors when processing 490,000+ rows.

---

## Step-by-Step Execution Sequence

Follow this exact order to build the project from scratch.

### Phase 1: Database Creation
Open **MySQL Workbench** and run these scripts in order:
1. `sql/staging/01_staging_ddl.sql`
2. `sql/oltp/02_oltp_ddl.sql`
3. `sql/warehouse/03_olap_ddl.sql`
4. `sql/procedures/04_etl_procedures.sql`

### Phase 2: Execute the Pipeline (Python)
Open your terminal in VS Code (ensure `.venv` is activated) and run:
1. `python src/etls/run_oltp_load.py`
    *   *Expected Output:* Loads raw data into Staging, then moves ~100k employees, ~141k assignments, and ~491k reviews into the OLTP database.
2. `python src/etls/run_dw_etl.py`
    *   *Expected Output:* Executes the procedures to populate the Data Warehouse. It will take 60–90 seconds to load the Fact tables and will print reconciliation success messages.

### Phase 3: Verify the Data Warehouse
Run this query in MySQL Workbench to confirm the Star Schema is fully populated:
```sql
USE employee_dw;
SELECT COUNT(*) FROM Dim_Employee;                 -- Expected: ~160,136
SELECT COUNT(*) FROM Dim_Department;               -- Expected: 3
SELECT COUNT(*) FROM Fact_PerformanceReviews;      -- Expected: ~491,000
SELECT COUNT(*) FROM Fact_ProjectAllocations;      -- Expected: ~141,000