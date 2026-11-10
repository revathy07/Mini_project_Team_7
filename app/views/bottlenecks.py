import plotly.express as px
import streamlit as st

from app import data
from src.database.exceptions import DataAccessError

PRIORITIES = ["Low", "Medium", "High", "Critical"]
BANDS = ["0 (unassigned)", "1-50", "51-100", "101-150", "151+"]

st.title("Project bottlenecks")

try:
    dept_map = data.departments()
    delay = data.project_delay_summary()
    overdue = data.overdue_projects(25)
except DataAccessError as err:
    st.error(f"Could not load project data: {err}")
    st.stop()

# ---------- delay ----------
st.subheader("Schedule slippage on completed projects")
st.caption("Delay = actual end minus planned end. Negative means early.")

if delay.empty:
    st.info("No completed projects.")
else:
    fig = px.bar(delay, x="department_name", y="avg_delay_days", color="priority",
                 barmode="group", category_orders={"priority": PRIORITIES},
                 hover_data={"projects": ":,", "pct_delayed": ":.1f"},
                 labels={"department_name": "", "avg_delay_days": "Average delay (days)",
                         "priority": "Priority"})
    st.plotly_chart(fig)

st.subheader("Open projects past their planned end")
total_overdue = int(overdue["total_overdue"].iloc[0]) if not overdue.empty else 0
st.metric("Overdue open projects", f"{total_overdue:,}",
          help="Active or on-hold projects whose planned end date is before today.")
st.caption("Showing the 25 most overdue.")
st.dataframe(
    overdue.drop(columns="total_overdue").rename(columns={
        "project_code": "Code", "project_name": "Project",
        "department_name": "Department", "priority": "Priority",
        "status": "Status", "planned_end_date": "Planned end",
        "days_overdue": "Days overdue", "budget": "Budget"}),
    hide_index=True)

# ---------- allocation ----------
st.divider()
st.subheader("Employee over-allocation")
dept_id = st.selectbox(
    "Department", options=[None, *dept_map], key="alloc_dept",
    format_func=lambda d: "All departments" if d is None else dept_map[d])

try:
    bands = data.allocation_bands(dept_id)
    over = data.overallocated_employees(dept_id, 25)
except DataAccessError as err:
    st.error(f"Could not load allocation data: {err}")
    st.stop()

total_over = int(over["total_overallocated"].iloc[0]) if not over.empty else 0
st.metric("Employees allocated above 100%", f"{total_over:,}",
          help="Sum of allocation % across open assignments of active employees.")

left, right = st.columns([2, 3])
with left:
    if bands.empty:
        st.info("No data.")
    else:
        fig = px.bar(bands, x="band", y="employees", text_auto=",",
                     category_orders={"band": BANDS},
                     labels={"band": "Total allocation %", "employees": "Active employees"})
        st.plotly_chart(fig)
with right:
    st.markdown("**Most over-allocated**")
    st.dataframe(
        over.drop(columns="total_overallocated").rename(columns={
            "employee_code": "Code", "full_name": "Name",
            "department_name": "Department",
            "open_assignments": "Open projects",
            "total_allocation": "Total allocation %"}),
        hide_index=True)