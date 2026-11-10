from datetime import date

import streamlit as st

from app import data
from src.database.exceptions import DataAccessError

st.title("Employees")

try:
    dept_map = data.departments()
except DataAccessError as err:
    st.error(f"Could not load departments: {err}")
    st.stop()

tab_onboard, tab_find = st.tabs(["Onboard employee", "Find employees"])

# ---------------------------------------------------------------
# Onboard
# ---------------------------------------------------------------
with tab_onboard:
    st.caption("Employee code (EMP-######) is generated automatically.")

    # Department sits OUTSIDE the form so roles and managers update when it changes
    dept_id = st.selectbox("Department", options=list(dept_map),
                           format_func=dept_map.get, key="onb_dept")
    try:
        roles = data.job_roles(dept_id)
        managers = data.managers(dept_id)
    except DataAccessError as err:
        st.error(f"Could not load options: {err}")
        st.stop()

    with st.form("onboard_employee"):
        c1, c2 = st.columns(2)
        first_name = c1.text_input("First name")
        last_name = c2.text_input("Last name")
        email = st.text_input("Work email")

        c3, c4, c5 = st.columns(3)
        gender = c3.selectbox("Gender", ["Male", "Female"])
        age = c4.number_input("Age", min_value=18, max_value=70, value=30)
        hire_date = c5.date_input("Hire date", value=date.today())

        c6, c7 = st.columns(2)
        job_role = c6.selectbox("Job role", roles)
        job_level = c7.selectbox("Job level", [1, 2, 3, 4, 5])

        income = st.number_input("Monthly income", min_value=1.0,
                                 value=5000.0, step=100.0)
        manager_id = st.selectbox(
            "Manager (optional)", options=[None, *managers],
            format_func=lambda m: "none" if m is None else managers[m])

        with st.expander("Work details (optional)"):
            overtime = st.checkbox("Works overtime")
            travel = st.selectbox(
                "Business travel",
                ["Non-Travel", "Travel_Rarely", "Travel_Frequently"], index=1)
            distance = st.number_input("Distance from home (km)",
                                       min_value=0, max_value=100, value=5)
            experience = st.number_input("Total working years",
                                         min_value=0, max_value=50, value=0)

        submitted = st.form_submit_button("Create employee")

    if submitted:
        try:
            employee_id, code, warning = data.onboard_employee(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                email=email.strip().lower(),
                gender=gender,
                age=int(age),
                hire_date=hire_date,
                department_id=dept_id,
                job_role=job_role,
                job_level=job_level,
                monthly_income=float(income),
                manager_id=manager_id,
                overtime=overtime,
                business_travel=travel,
                distance_from_home=int(distance),
                total_working_years=int(experience),
            )
        except DataAccessError as err:
            st.error(str(err))
        else:
            st.success(f"Created {first_name} {last_name}. Code {code} (ID {employee_id}).")
            if warning:
                st.warning(warning)

# ---------------------------------------------------------------
# Find
# ---------------------------------------------------------------
with tab_find:
    f1, f2, f3 = st.columns([3, 2, 1])
    term = f1.text_input("Search name, code or email", key="emp_term")
    dept_filter = f2.selectbox(
        "Department", options=[None, *dept_map], key="emp_dept_filter",
        format_func=lambda d: "All departments" if d is None else dept_map[d])
    active_only = f3.checkbox("Active only", value=True)

    try:
        results = data.employee_search(term, dept_filter, active_only)
    except DataAccessError as err:
        st.error(f"Search failed: {err}")
    else:
        st.caption(f"{len(results)} shown (max 50, newest first).")
        st.dataframe(results, hide_index=True)