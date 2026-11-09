import plotly.express as px
import streamlit as st
from mysql.connector import Error as MySQLError

from app import data
from src.database.exceptions import DataAccessError

st.title("Workforce overview")
st.caption("Source: data warehouse (star schema). Figures refresh every 10 minutes.")

try:
    with st.spinner("Loading dashboard..."):
        kpi = data.kpis()
        trend = data.yearly_trend()
        dept_perf = data.department_performance()
        headcount = data.department_headcount()
        projects = data.project_status()
except (DataAccessError, MySQLError) as err:
    st.error(f"Could not load the dashboard: {err}")
    st.stop()

# ---------- KPI row ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active employees", f"{kpi['active_employees']:,}")
c2.metric("Attrition rate", f"{kpi['attrition_rate']:.1f}%",
          help=f"{kpi['employees_left']:,} employees have left.")
c3.metric("Average performance score", f"{kpi['avg_score']:.2f} / 5")
c4.metric("Reviews on record", f"{kpi['total_reviews']:,}")

# ---------- year-over-year trend ----------
st.subheader("Year-over-year performance")
hide_partial = st.toggle("Hide years with very few reviews", value=True,
                         help="Hides partial years (under 5% of the busiest year's reviews).")

if trend.empty:
    st.info("No review data yet.")
else:
    shown = trend
    if hide_partial:
        shown = trend[trend["total_reviews"] >= 0.05 * trend["total_reviews"].max()]
    fig = px.line(
        shown, x="year", y="average_performance", markers=True,
        hover_data={"total_reviews": ":,", "average_rating": ":.2f"},
        labels={"year": "Review year", "average_performance": "Average score (1-5)"},
    )
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig)

# ---------- department views ----------
left, right = st.columns(2)

with left:
    st.subheader("Performance by department")
    if dept_perf.empty:
        st.info("No data.")
    else:
        fig = px.bar(
            dept_perf.sort_values("average_performance"),
            x="average_performance", y="department_name", orientation="h",
            text_auto=".2f",
            hover_data={"average_goal_achievement": ":.1f", "total_reviews": ":,"},
            labels={"average_performance": "Average score (1-5)", "department_name": ""},
        )
        st.plotly_chart(fig)

with right:
    st.subheader("Active headcount by department")
    if headcount.empty:
        st.info("No data.")
    else:
        fig = px.pie(headcount, names="department_name", values="employee_count", hole=0.45)
        st.plotly_chart(fig)

# ---------- projects and detail table ----------
left, right = st.columns(2)

with left:
    st.subheader("Projects by status")
    if projects.empty:
        st.info("No data.")
    else:
        fig = px.bar(projects, x="status", y="project_count", text_auto=True,
                     labels={"status": "", "project_count": "Projects"})
        st.plotly_chart(fig)

with right:
    st.subheader("Department detail")
    st.dataframe(
        dept_perf.rename(columns={
            "department_name": "Department",
            "average_performance": "Avg score",
            "average_goal_achievement": "Avg goal achievement %",
            "total_reviews": "Reviews",
        }),
        hide_index=True,
    )