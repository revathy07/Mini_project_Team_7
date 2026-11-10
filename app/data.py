"""UI-facing data access: cached DataFrames built from AnalyticsManager.
No SQL lives here or in the pages."""
from datetime import date, timedelta

from src.database.exceptions import ValidationError

import pandas as pd
import streamlit as st

from src.database.exceptions import DataAccessError
from src.entities.review import Review
from src.managers.review_manager import ReviewManager
from src.managers.warehouse_sync import WarehouseSync

from src.entities.employee import Employee
from src.entities.project import Project
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager

from src.database.db_manager import DatabaseConnection
from src.managers.analytics_manager import AnalyticsManager
from src.managers.oltp_analytics_manager import OltpAnalyticsManager
from app.iam import require_permission

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
    rows = _employees().search_employees(
        term, department_id, active_only, limit=50)
    cols = ["employee_code", "full_name", "email", "department_name",
            "job_role", "job_level", "monthly_income", "hire_date", "status"]
    return _frame(rows, cols, numeric=["monthly_income"])

@st.cache_data(ttl=60, show_spinner=False)
def project_search(term, department_id, status):
    rows = _projects().search_projects(term, department_id, status, limit=50)
    cols = ["project_code", "project_name", "department_name", "status",
            "priority", "start_date", "planned_end_date", "end_date", "budget"]
    return _frame(rows, cols, numeric=["budget"])
# ---------------------------------------------------------------
# Reviews: form support + warehouse sync
# ---------------------------------------------------------------
@st.cache_resource
def _reviews():
    return ReviewManager()


@st.cache_resource
def _warehouse():
    return WarehouseSync()


def employee_choices(term):
    """{employee_id: label} for up to 20 active matches. Needs 2+ characters,
    so the 100K-row table is never listed."""
    term = (term or "").strip()
    if len(term) < 2:
        return {}
    rows = _employees().search_employees(term, None, True, limit=20)
    return {
        row["employee_id"]:
            f"{row['full_name']} ({row['employee_code']}) - {row['department_name']}"
        for row in rows
    }


def employee_summary(employee_id):
    return _employees().get_employee_summary(employee_id)


def employee_review_history(employee_id):
    rows = _reviews().list_employee_reviews(employee_id, 10)
    cols = ["review_date", "review_period", "performance_score", "performance_rating",
            "goal_achievement_pct", "peer_feedback_score", "promotion_recommended"]
    return _frame(rows, cols, numeric=cols[2:6])


def sync_reviews():
    """New hires first (so their reviews can load), then reviews."""
    require_permission("sync_warehouse")
    _sync_reviews()


def _sync_reviews():
    _warehouse().refresh_employees(date.today())
    _warehouse().refresh_reviews()
    st.cache_data.clear()


def submit_review(**fields):
    """Save a review in OLTP, then try to sync it to the warehouse.
    OLTP save failing raises DataAccessError. Sync failing does NOT raise:
    the review is saved, and the result carries a warning to show."""
    require_permission("submit_reviews")

    review = Review(**fields)
    review_id = _reviews().create_review(review)     # committed here

    result = {"review_id": review_id, "synced": False, "warning": None}
    try:
        _sync_reviews()
        result["synced"] = _warehouse().is_review_loaded(review_id)
        if not result["synced"]:
            result["warning"] = (
                "Saved. The warehouse has no version of this employee covering "
                "the review date yet, so dashboards will not count it until it does.")
    except DataAccessError as err:
        result["warning"] = f"Saved, but the warehouse refresh failed: {err}"
    return result

def onboard_employee(**fields):
    """Create an employee, then give them a first warehouse version.
    Returns (employee_id, employee_code, warning). Warning is None when synced.
    Raises DataAccessError if the OLTP save fails."""
    require_permission("manage_employees")
    employee = Employee(employee_code="PENDING", **fields)
    employee_id, code = _employees().create_employee(employee)   # committed
    employee_search.clear()
    managers.clear()

    warning = None
    try:
        sync_employees(date.today())
    except DataAccessError as err:
        warning = (f"Saved, but the warehouse sync failed: {err}. "
                   "Dashboards will not include this employee until it succeeds.")
    return employee_id, code, warning


def register_project(**fields):
    """Create a project. Returns (project_id, project_code)."""
    require_permission("manage_projects")
    project = Project(project_code="PENDING", **fields)
    result = _projects().create_project(project)
    project_search.clear()
    return result

# ---------------------------------------------------------------
# Edit employee: SCD2 hook
# ---------------------------------------------------------------
def sync_employees(effective_date=None):
    """Push new hires and job changes to Dim_Employee, then drop cached data."""
    require_permission("sync_warehouse")
    _warehouse().refresh_employees(effective_date or date.today())
    st.cache_data.clear()


def employee_for_edit(employee_id):
    return _employees().get_employee_for_edit(employee_id)


def version_history(employee_code):
    rows = _warehouse().version_history(employee_code)
    cols = ["department_name", "job_role", "job_level", "monthly_income",
            "start_date", "end_date", "is_current"]
    return _frame(rows, cols, numeric=["job_level", "monthly_income"])


def change_floor(employee_id, employee_code):
    """Earliest effective date allowed for a change. If the employee has no
    warehouse version yet, load it FIRST, so the pre-change state is kept as
    history instead of being replaced by the new values."""
    floor = _employees().get_change_floor(employee_id)
    dw_start = _warehouse().current_version_start(employee_code)
    if dw_start is None:
        sync_employees(date.today())                  # may raise WarehouseSyncError
        dw_start = _warehouse().current_version_start(employee_code)
    if dw_start is not None and dw_start + timedelta(days=1) > floor:
        floor = dw_start + timedelta(days=1)          # a version needs >= 1 day
    return floor


def apply_job_change(employee_id, employee_code, changes, effective_date):
    """Save in OLTP (with change log), then version the employee in the warehouse.
    OLTP failure raises DataAccessError. Warehouse failure does NOT raise:
    the change is saved and the result carries a warning."""
    require_permission("manage_employees")
    if any(key != "manager_id" for key in changes):
        floor = change_floor(employee_id, employee_code)
        if effective_date < floor:
            raise ValidationError(
                f"Effective date cannot be before {floor} (the current warehouse "
                "version, a review, or a project assignment starts then).")

    outcome = _employees().update_job_details(employee_id, changes, effective_date)
    employee_search.clear()

    result = {**outcome, "synced": True, "warning": None}
    if outcome["diffs"]:
        try:
            sync_employees(effective_date)
        except DataAccessError as err:
            result["synced"] = False
            result["warning"] = (
                f"Saved, but the warehouse sync failed: {err}. Use "
                "'Retry warehouse sync' on this page. Do it today, because the "
                "retry dates the change today.")
    return result