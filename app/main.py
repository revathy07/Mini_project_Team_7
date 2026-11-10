import sys
from pathlib import Path

# Make `src` importable: `streamlit run app/main.py` only puts app/ on the path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import data
from app.iam import (
    AuthenticationError,
    can,
    current_user,
    initialize_iam,
    login,
    logout,
)

st.set_page_config(page_title="Employee Analytics", page_icon="📊", layout="wide")

try:
    initialize_iam()
    user = current_user()
except AuthenticationError as err:
    st.error(str(err))
    st.stop()

if user is None:
    st.title("Employee Analytics")
    st.subheader("Sign in")
    st.caption(
        "First-time setup? Run `uv run python -m src.auth.bootstrap_admin` "
        "from the project folder to create the first administrator."
    )
    with st.form("sign_in", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        try:
            if login(username, password):
                st.rerun()
            st.error("Sign-in failed. Check your username and password, or contact an administrator.")
        except AuthenticationError as err:
            st.error(str(err))
    st.stop()

pages = [
    st.Page("views/overview.py", title="Overview", icon="📊", default=True),
    st.Page("views/performance.py", title="Performance", icon="🏆"),
    st.Page("views/attrition.py", title="Attrition", icon="⚠️"),
    st.Page("views/bottlenecks.py", title="Bottlenecks", icon="🚧"),
]
if user["role"] in ("Admin", "HR"):
    pages.extend([
        st.Page("views/employees.py", title="Employees", icon="👥"),
        st.Page("views/projects.py", title="Projects", icon="📁"),
        st.Page("views/reviews.py", title="Reviews", icon="📝"),
    ])
if can(user, "manage_employees"):
    pages.append(st.Page("views/edit_employee.py", title="Edit employee", icon="✏️"))
if can(user, "manage_users"):
    pages.append(st.Page("views/access.py", title="User access", icon="🔐"))

navigation = st.navigation(pages)

with st.sidebar:
    st.write(f"Signed in as **{user['username']}** ({user['role']})")
    if st.button("Sign out"):
        logout()
        st.rerun()

    st.subheader("System status")
    try:
        status = data.database_status()
    except ValueError as err:
        st.error(f"Configuration error: {err}")
        status = {}

    for name, is_up in status.items():
        st.write(f"{'🟢' if is_up else '🔴'} {name}")

    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

navigation.run()