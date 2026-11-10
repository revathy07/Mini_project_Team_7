"""UI-facing data access: cached DataFrames built from AnalyticsManager.
No SQL lives here or in the pages."""
import pandas as pd
import streamlit as st

from src.entities.employee import Employee
from src.entities.project import Project
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager

from src.database.db_manager import DatabaseConnection
from src.managers.analytics_manager import AnalyticsManager
from src.managers.oltp_analytics_manager import OltpAnalyticsManager

CACHE_SECONDS = 600


@st.cache_resource
def _analytics():
    return AnalyticsManager()


def _frame(rows, columns, numeric=()):
    """List of dict rows -> DataFrame. MySQL returns Decimal; convert to float."""
    df = pd.DataFrame(rows, columns=columns)
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=30, show_spinner=False)
def database_status():
    db = DatabaseConnection()
    return {
        "OLTP database": db.ping(db.database_for("oltp")),
        "Data warehouse": db.ping(db.database_for("dw")),
    }


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def kpis():
    analytics = _analytics()
    attrition = analytics.get_attrition_statistics()
    performance = analytics.get_average_performance()
    return {
        "active_employees": int(attrition["active_employees"] or 0),
        "employees_left": int(attrition["employees_left"] or 0),
        "attrition_rate": float(attrition["attrition_rate"] or 0),
        "avg_score": float(performance["average_performance_score"] or 0),
        "avg_goal": float(performance["average_goal_achievement"] or 0),
        "total_reviews": int(performance["total_reviews"] or 0),
    }


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def yearly_trend():
    rows = _analytics().get_yearly_performance_trend()
    cols = ["year", "average_performance", "average_rating", "total_reviews"]
    return _frame(rows, cols, numeric=cols)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def department_performance():
    rows = _analytics().get_department_performance()
    cols = ["department_name", "average_performance",
            "average_goal_achievement", "total_reviews"]
    return _frame(rows, cols, numeric=cols[1:])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def department_headcount():
    rows = _analytics().get_department_distribution()
    cols = ["department_name", "employee_count"]
    return _frame(rows, cols, numeric=["employee_count"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def project_status():
    rows = _analytics().get_project_status_distribution()
    cols = ["status", "project_count"]
    return _frame(rows, cols, numeric=["project_count"])

# ---------------------------------------------------------------
# Dashboards: performance, attrition, bottlenecks
# ---------------------------------------------------------------
@st.cache_resource
def _oltp_analytics():
    return OltpAnalyticsManager()


@st.cache_data(ttl=3600, show_spinner=False)
def review_year_range():
    row = _analytics().get_review_year_range()
    return int(row["min_year"]), int(row["max_year"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def yearly_trend_by_department(year_from, year_to):
    rows = _analytics().get_yearly_trend_by_department()
    cols = ["year", "department_name", "avg_score", "reviews"]
    df = _frame(rows, cols, numeric=["year", "avg_score", "reviews"])
    return df[df["year"].between(year_from, year_to)]


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def top_performers(year_from, year_to, min_reviews, top_n):
    rows = _analytics().get_top_performers(year_from, year_to, min_reviews, top_n)
    cols = ["department_name", "dept_rank", "employee_code", "full_name",
            "job_role", "avg_score", "avg_goal", "review_count"]
    return _frame(rows, cols, numeric=["dept_rank", "avg_score", "avg_goal", "review_count"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def attrition_by_factor(department_id):
    rows = _oltp_analytics().get_attrition_by_factor(department_id)
    df = _frame(rows, ["factor", "bucket", "headcount", "leavers"],
                numeric=["headcount", "leavers"])
    df["attrition_rate"] = (100 * df["leavers"] / df["headcount"]).round(1)
    return df


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def risk_distribution(department_id):
    rows = _oltp_analytics().get_risk_distribution(department_id)
    return _frame(rows, ["risk_score", "employees"], numeric=["risk_score", "employees"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def high_risk_employees(department_id, limit=25):
    rows = _oltp_analytics().get_high_risk_employees(department_id, limit)
    cols = ["employee_code", "full_name", "department_name", "job_role",
            "risk_score", "risk_factors"]
    return _frame(rows, cols, numeric=["risk_score"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def project_delay_summary():
    rows = _analytics().get_project_delay_summary()
    cols = ["department_name", "priority", "projects", "avg_delay_days", "pct_delayed"]
    return _frame(rows, cols, numeric=cols[2:])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def overdue_projects(limit=25):
    rows = _analytics().get_overdue_projects(limit)
    cols = ["project_code", "project_name", "department_name", "priority", "status",
            "planned_end_date", "days_overdue", "budget", "total_overdue"]
    return _frame(rows, cols, numeric=["days_overdue", "budget", "total_overdue"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def allocation_bands(department_id):
    rows = _oltp_analytics().get_allocation_bands(department_id)
    return _frame(rows, ["band", "employees"], numeric=["employees"])


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def overallocated_employees(department_id, limit=25):
    rows = _oltp_analytics().get_overallocated_employees(department_id, limit)
    cols = ["employee_code", "full_name", "department_name", "open_assignments",
            "total_allocation", "total_overallocated"]
    return _frame(rows, cols, numeric=cols[3:])

# ---------------------------------------------------------------
# OLTP: lookups, search, and writes (used by the form pages)
# ---------------------------------------------------------------
@st.cache_resource
def _employees():
    return EmployeeManager()


@st.cache_resource
def _projects():
    return ProjectManager()


@st.cache_data(ttl=3600, show_spinner=False)
def departments():
    """{department_id: department_name}, sorted by name."""
    rows = _employees().list_departments()
    return {row["department_id"]: row["department_name"] for row in rows}


@st.cache_data(ttl=3600, show_spinner=False)
def job_roles(department_id):
    return _employees().list_job_roles(department_id)


@st.cache_data(ttl=300, show_spinner=False)
def managers(department_id):
    """{employee_id: 'Name (EMP-000123)'} for the manager dropdown."""
    rows = _employees().list_managers(department_id)
    return {row["employee_id"]: row["label"] for row in rows}


@st.cache_data(ttl=60, show_spinner=False)
def employee_search(term, department_id, active_only):
    rows = _employees().search_employees(term, department_id, active_only, limit=50)
    cols = ["employee_code", "full_name", "email", "department_name",
            "job_role", "job_level", "monthly_income", "hire_date", "status"]
    return _frame(rows, cols, numeric=["monthly_income"])


@st.cache_data(ttl=60, show_spinner=False)
def project_search(term, department_id, status):
    rows = _projects().search_projects(term, department_id, status, limit=50)
    cols = ["project_code", "project_name", "department_name", "status",
            "priority", "start_date", "planned_end_date", "end_date", "budget"]
    return _frame(rows, cols, numeric=["budget"])


def onboard_employee(**fields):
    """Create an employee. Returns (employee_id, employee_code).
    Raises DataAccessError (ValidationError, DuplicateRecordError, ...)."""
    employee = Employee(employee_code="PENDING", **fields)
    result = _employees().create_employee(employee)
    employee_search.clear()
    managers.clear()
    return result


def register_project(**fields):
    """Create a project. Returns (project_id, project_code)."""
    project = Project(project_code="PENDING", **fields)
    result = _projects().create_project(project)
    project_search.clear()
    return result