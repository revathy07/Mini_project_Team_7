from datetime import date, timedelta

import streamlit as st

from app import data
from app.iam import can, current_user
from src.database.exceptions import DataAccessError

st.title("Projects")
can_manage = can(current_user(), "manage_projects")

try:
    dept_map = data.departments()
except DataAccessError as err:
    st.error(f"Could not load departments: {err}")
    st.stop()

tab_create, tab_browse = st.tabs(["Create project", "Browse projects"])

# ---------------------------------------------------------------
# Create
# ---------------------------------------------------------------
with tab_create:
    st.caption("Project code (PROJ-#####) is generated automatically.")

    dept_id = st.selectbox("Owning department", options=list(dept_map),
                           format_func=dept_map.get, key="proj_dept")
    try:
        managers = data.managers(dept_id)
    except DataAccessError as err:
        st.error(f"Could not load managers: {err}")
        st.stop()

    with st.form("create_project"):
        name = st.text_input("Project name")

        c1, c2, c3 = st.columns(3)
        start_date = c1.date_input("Start date", value=date.today())
        planned_end = c2.date_input("Planned end date",
                                    value=date.today() + timedelta(days=180))
        budget = c3.number_input("Budget", min_value=0.0,
                                 value=100000.0, step=5000.0)

        c4, c5 = st.columns(2)
        priority = c4.selectbox("Priority", ["Low", "Medium", "High", "Critical"],
                                index=1)
        status = c5.selectbox("Status", ["Active", "On Hold"])

        manager_id = st.selectbox(
            "Project manager (optional)", options=[None, *managers],
            format_func=lambda m: "none" if m is None else managers[m])

        submitted = st.form_submit_button(
            "Create project", disabled=not can_manage
        )

    if submitted and can_manage:
        try:
            project_id, code = data.register_project(
                project_name=name.strip(),
                department_id=dept_id,
                project_manager_id=manager_id,
                start_date=start_date,
                planned_end_date=planned_end,
                budget=float(budget),
                status=status,
                priority=priority,
            )
        except DataAccessError as err:
            st.error(str(err))
        else:
            st.success(f"Created project {name}. Code {code} (ID {project_id}).")

# ---------------------------------------------------------------
# Browse
# ---------------------------------------------------------------
with tab_browse:
    f1, f2, f3 = st.columns([3, 2, 2])
    term = f1.text_input("Search name or code", key="proj_term")
    dept_filter = f2.selectbox(
        "Department", options=[None, *dept_map], key="proj_dept_filter",
        format_func=lambda d: "All departments" if d is None else dept_map[d])
    status_filter = f3.selectbox(
        "Status", options=[None, "Active", "On Hold", "Completed", "Cancelled"],
        key="proj_status_filter",
        format_func=lambda s: "All statuses" if s is None else s)

    try:
        results = data.project_search(term, dept_filter, status_filter)
    except DataAccessError as err:
        st.error(f"Search failed: {err}")
    else:
        st.caption(f"{len(results)} shown (max 50, newest first).")
        st.dataframe(results, hide_index=True)