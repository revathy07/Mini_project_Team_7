"""UI-facing data access: cached DataFrames built from AnalyticsManager.
No SQL lives here or in the pages."""
import pandas as pd
import streamlit as st

from src.database.db_manager import DatabaseConnection
from src.managers.analytics_manager import AnalyticsManager

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