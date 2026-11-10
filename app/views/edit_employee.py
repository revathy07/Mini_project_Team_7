from datetime import date

import streamlit as st

from app import data
from app.iam import require_permission
from src.database.exceptions import DataAccessError

require_permission("manage_employees")

st.title("Edit employee")
st.caption("Department, role, level and pay changes are versioned in the "
           "warehouse (SCD Type 2): the old row closes on the effective date "
           "and a new row opens the same day. History is kept.")


def show_result(result):
    st.success(f"Saved: {result['change_type'] or 'manager updated'}")
    for field, old, new in result["diffs"]:
        st.markdown(f"- **{field}**: {old} → {new}")
    if result["manager_changed"]:
        st.markdown("- **manager** updated (not versioned)")
    if result["warning"]:
        st.warning(result["warning"])
    elif result["diffs"]:
        st.success("Warehouse updated. See the new version row below.")


flash = st.session_state.pop("edit_result", None)
if flash:
    show_result(flash)

with st.expander("Warehouse sync"):
    st.caption("Runs automatically after each save. Use the button to retry "
               "after a failure (dated today).")
    if st.button("Retry warehouse sync"):
        try:
            data.sync_employees()
        except DataAccessError as err:
            st.error(str(err))
        else:
            st.success("Warehouse is up to date.")

# ---------- pick employee ----------
term = st.text_input("Find employee (name, code or email, at least 2 characters)",
                     key="edit_term")
try:
    choices = data.employee_choices(term)
except DataAccessError as err:
    st.error(f"Search failed: {err}")
    st.stop()

if not choices:
    st.info("Type at least 2 characters." if len(term.strip()) < 2
            else "No active employee matches.")
    st.stop()

employee_id = st.selectbox("Employee", options=list(choices),
                           format_func=choices.get, key="edit_pick")

try:
    emp = data.employee_for_edit(employee_id)
    dept_map = data.departments()
    floor = data.change_floor(employee_id, emp["employee_code"])
except DataAccessError as err:
    st.error(f"Could not load employee: {err}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Department", emp["department_name"])
c2.metric("Role", emp["job_role"])
c3.metric("Level", emp["job_level"])
c4.metric("Monthly income", f"{float(emp['monthly_income']):,.2f}")
st.caption(f"{emp['full_name']} ({emp['employee_code']}), manager: "
           f"{emp['manager_name'] or 'none'}")

today = date.today()
if floor > today:
    st.warning(f"Changes cannot be dated before {floor}, which is after today. "
               "Try again on that date.")
else:
    # Department is OUTSIDE the form so roles and managers follow it
    dept_ids = list(dept_map)
    new_dept = st.selectbox(
        "Department", options=dept_ids, index=dept_ids.index(emp["department_id"]),
        format_func=dept_map.get, key=f"edit_dept_{employee_id}")
    roles = data.job_roles(new_dept)

    manager_chosen, new_manager = False, None
    if new_dept != emp["department_id"]:
        mgrs = data.managers(new_dept)
        new_manager = st.selectbox(
            "New manager (department changed)", options=[None, *mgrs],
            format_func=lambda m: "none" if m is None else mgrs[m],
            key=f"edit_mgr_{employee_id}_{new_dept}")
        manager_chosen = True

    with st.form(f"edit_form_{employee_id}"):
        role_index = roles.index(emp["job_role"]) if emp["job_role"] in roles else 0
        job_role = st.selectbox("Job role", roles, index=role_index)
        level = st.selectbox("Job level", [1, 2, 3, 4, 5],
                             index=int(emp["job_level"] or 1) - 1)
        income = st.number_input("Monthly income", min_value=1.0,
                                 value=float(emp["monthly_income"]), step=100.0)
        effective = st.date_input("Effective date", value=today,
                                  min_value=floor, max_value=today,
                                  help="The day the new version starts in the warehouse.")
        submitted = st.form_submit_button("Save changes")

    if submitted:
        changes = {}
        if new_dept != emp["department_id"]:
            changes["department_id"] = new_dept
        if job_role != emp["job_role"]:
            changes["job_role"] = job_role
        if level != emp["job_level"]:
            changes["job_level"] = level
        if round(float(income), 2) != round(float(emp["monthly_income"]), 2):
            changes["monthly_income"] = income
        if manager_chosen:
            changes["manager_id"] = new_manager

        if not changes:
            st.info("Nothing changed.")
        else:
            try:
                result = data.apply_job_change(
                    employee_id, emp["employee_code"], changes, effective)
            except DataAccessError as err:
                st.error(str(err))
            else:
                st.session_state["edit_result"] = result
                st.rerun()

# ---------- version history from the warehouse ----------
st.subheader("Warehouse version history")
try:
    history = data.version_history(emp["employee_code"])
except DataAccessError as err:
    st.error(f"Could not load history: {err}")
else:
    st.caption("end date 9999-12-31 = still current. Each end date equals the "
               "next row's start date.")
    st.dataframe(history.rename(columns={
        "department_name": "Department", "job_role": "Role", "job_level": "Level",
        "monthly_income": "Income", "start_date": "Start", "end_date": "End",
        "is_current": "Current"}), hide_index=True)