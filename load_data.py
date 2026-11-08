import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")

engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/employee_oltp")
engine_dw = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/employee_dw")
DATA_DIR = Path("data/processed")

print("1. Clearing old data from tables...")
with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    for tbl in ["Employee_Change_Log", "Performance_Reviews", "Project_Assignments", "Projects", "Employees", "Departments"]:
        conn.execute(text(f"TRUNCATE TABLE {tbl};"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

with engine_dw.begin() as conn_dw:
    conn_dw.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    conn_dw.execute(text("TRUNCATE TABLE Dim_Employee;"))
    conn_dw.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

print("2. Loading raw data into OLTP...")

with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # --- DEPARTMENTS ---
    df_dept = pd.read_csv(DATA_DIR / "departments.csv")
    df_dept['department_code'] = 'DEPT-' + df_dept['department_id'].astype(str)
    df_dept = df_dept.rename(columns={'annual_budget': 'budget'})
    df_dept = df_dept[['department_id', 'department_code', 'department_name', 'location', 'budget']]
    df_dept.to_sql('Departments', con=conn, if_exists='append', index=False)

    # --- EMPLOYEES ---
    df_emp = pd.read_csv(DATA_DIR / "employees.csv")
    df_emp['status'] = 'Active' 
    
    # THE FIX: Generate unique employee_code based on employee_id, not source IBM number
    df_emp['employee_code'] = df_emp['employee_id'].apply(lambda x: f"EMP-{x:06d}")
    df_emp['manager_id'] = df_emp['manager_id'].astype('Int64')
    
    oltp_emp_cols = ['employee_id', 'employee_code', 'first_name', 'last_name', 'email', 'hire_date', 'department_id', 'job_role', 'job_level', 'monthly_income', 'manager_id', 'attrition', 'status']
    df_emp = df_emp[[c for c in oltp_emp_cols if c in df_emp.columns]]
    df_emp.to_sql('Employees', con=conn, if_exists='append', index=False)

    # --- PROJECTS ---
    df_proj = pd.read_csv(DATA_DIR / "projects.csv")
    df_proj['project_code'] = 'PROJ-' + df_proj['project_id'].astype(str)
    df_proj['project_manager_id'] = None 
    oltp_proj_cols = ['project_id', 'project_code', 'project_name', 'department_id', 'project_manager_id', 'start_date', 'end_date', 'status']
    df_proj = df_proj[[c for c in oltp_proj_cols if c in df_proj.columns]]
    df_proj.to_sql('Projects', con=conn, if_exists='append', index=False)

    # --- PROJECT ASSIGNMENTS ---
    df_asg = pd.read_csv(DATA_DIR / "project_assignments.csv")
    df_asg = df_asg.rename(columns={'role': 'role_in_project', 'allocation_pct': 'allocation_percentage', 'assigned_date': 'start_date', 'released_date': 'end_date'})
    df_asg['status'] = 'Active'
    oltp_asg_cols = ['assignment_id', 'employee_id', 'project_id', 'role_in_project', 'allocation_percentage', 'start_date', 'end_date', 'status']
    df_asg = df_asg[[c for c in oltp_asg_cols if c in df_asg.columns]]
    df_asg.to_sql('Project_Assignments', con=conn, if_exists='append', index=False)

      # --- PERFORMANCE REVIEWS ---
    df_rev = pd.read_csv(DATA_DIR / "performance_reviews.csv")
    df_rev = df_rev.rename(columns={'review_cycle': 'review_period'})
    
    # THE FIX: Drop duplicate reviews for the same employee in the same period
    df_rev = df_rev.drop_duplicates(subset=['employee_id', 'review_period'], keep='last')
    
    df_rev['job_satisfaction'] = 3
    df_rev['work_life_balance'] = 3
    df_rev['percent_salary_hike'] = 0.0
    df_rev['comments'] = 'N/A'
    oltp_rev_cols = ['review_id', 'employee_id', 'reviewer_id', 'review_date', 'review_period', 'performance_rating', 'job_satisfaction', 'work_life_balance', 'percent_salary_hike', 'comments']
    df_rev = df_rev[[c for c in oltp_rev_cols if c in df_rev.columns]]
    df_rev.to_sql('Performance_Reviews', con=conn, if_exists='append', index=False)
    
    # --- EMPLOYEE CHANGE LOG ---
    df_change = pd.read_csv(DATA_DIR / "employee_changes.csv")
    df_log = df_change[df_change['version_no'] > 1].copy()
    df_log = df_log.rename(columns={'effective_start_date': 'change_date'})
    df_log['field_name'] = 'Multiple'
    df_log['old_value'] = 'Historical'
    df_log['new_value'] = 'Current'
    oltp_log_cols = ['employee_id', 'change_date', 'change_type', 'field_name', 'old_value', 'new_value']
    df_log = df_log[[c for c in oltp_log_cols if c in df_log.columns]]
    df_log.to_sql('Employee_Change_Log', con=conn, if_exists='append', index=False)

    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    conn.commit()

print("\n OLTP Data Loaded. Populating OLAP Data Warehouse...")

with engine_dw.connect() as conn_dw:
    # --- BUILD DIM_EMPLOYEE DIRECTLY FROM CSV ---
    dim_emp_hist = df_change.merge(df_emp[['employee_id', 'employee_code', 'first_name', 'last_name', 'email', 'hire_date', 'attrition']], on='employee_id')
    dim_emp_hist = dim_emp_hist.merge(df_dept[['department_id', 'department_name']], on='department_id')

    emp_no_changes = df_emp[~df_emp['employee_id'].isin(df_change['employee_id'])].copy()
    emp_no_changes = emp_no_changes.merge(df_dept[['department_id', 'department_name']], on='department_id')

    def format_dw(df, is_history=True):
        out = pd.DataFrame()
        out['employee_code'] = df['employee_code']
        out['full_name'] = df['first_name'] + ' ' + df['last_name']
        out['email'] = df['email']
        out['department_name'] = df['department_name']
        out['job_role'] = df['job_role']
        out['job_level'] = df['job_level']
        out['monthly_income'] = df['monthly_income']
        out['hire_date'] = df['hire_date']
        out['attrition_flag'] = df['attrition']
        out['start_date'] = df['effective_start_date'] if is_history else df['hire_date']
        out['end_date'] = df['effective_end_date'].fillna('9999-12-31') if is_history else '9999-12-31'
        out['is_current'] = df['is_current'] if is_history else 1
        return out

    dw_history = format_dw(dim_emp_hist, True)
    dw_current = format_dw(emp_no_changes, False)

    final_dim_emp = pd.concat([dw_history, dw_current])
    final_dim_emp.to_sql('Dim_Employee', con=conn_dw, if_exists='append', index=False)
    conn_dw.commit()

print(f" Loaded {len(final_dim_emp)} rows into Dim_Employee.")
print("\n ALL DATA LOADED!")