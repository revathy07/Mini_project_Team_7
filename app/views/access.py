import pandas as pd
import streamlit as st

from app.iam import require_permission
from src.auth.iam import (
    AuthenticationError,
    ROLES,
    create_user,
    list_users,
    reset_user_password,
    set_user_active,
    update_user_role,
)

admin = require_permission("manage_users")
st.title("User access")
st.caption(
    "Create named accounts with least-privilege roles for HR and Executive users."
)

st.subheader("Add an account")
role = st.selectbox("Role", ROLES, key="new_role")

with st.form("create_iam_user", clear_on_submit=True):
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Temporary password (at least 12 characters)",
                             type="password")
    confirmation = st.text_input("Confirm temporary password", type="password")
    create_submitted = st.form_submit_button("Create account")

if create_submitted:
    if password != confirmation:
        st.error("Passwords do not match.")
    else:
        try:
            create_user(username, email, password, role)
        except AuthenticationError as err:
            st.error(str(err))
        else:
            st.success(f"Created the {role} account for {username.strip()}.")
            st.rerun()

st.divider()
st.subheader("Manage accounts")
try:
    accounts = list_users()
except AuthenticationError as err:
    st.error(str(err))
    st.stop()

if not accounts:
    st.info("No accounts were found.")
else:
    visible = pd.DataFrame(accounts).drop(
        columns=["user_id", "employee_id", "employee_name"], errors="ignore"
    )
    st.dataframe(visible, hide_index=True)

    account_labels = {
        row["user_id"]: f"{row['username']} ({row['role']})"
        for row in accounts
    }
    selected_id = st.selectbox(
        "Select an account", options=list(account_labels),
        format_func=account_labels.get,
    )
    selected = next(row for row in accounts if row["user_id"] == selected_id)
    selected_role = st.selectbox(
        "Assigned role", ROLES, index=ROLES.index(selected["role"]),
        key=f"role_{selected_id}",
    )

    c1, c2 = st.columns(2)
    if c1.button("Save role", key=f"save_role_{selected_id}"):
        try:
            update_user_role(selected_id, selected_role)
        except AuthenticationError as err:
            st.error(str(err))
        else:
            st.success("Role updated.")
            st.rerun()

    if selected_id == admin["user_id"]:
        st.info("You cannot deactivate your own account.")
    elif c2.button(
        "Deactivate account" if selected["is_active"] else "Reactivate account",
        key=f"toggle_{selected_id}",
    ):
        try:
            set_user_active(selected_id, not selected["is_active"], admin["user_id"])
        except AuthenticationError as err:
            st.error(str(err))
        else:
            st.success("Account status updated.")
            st.rerun()

    with st.form(f"reset_password_{selected_id}", clear_on_submit=True):
        new_password = st.text_input("Set a new password", type="password")
        new_confirmation = st.text_input(
            "Confirm new password", type="password"
        )
        reset_submitted = st.form_submit_button("Reset password")
    if reset_submitted:
        if new_password != new_confirmation:
            st.error("Passwords do not match.")
        else:
            try:
                reset_user_password(selected_id, new_password)
            except AuthenticationError as err:
                st.error(str(err))
            else:
                st.success("Password reset.")
