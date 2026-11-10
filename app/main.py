import sys
from pathlib import Path

# Make `src` importable: `streamlit run app/main.py` only puts app/ on the path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import data

st.set_page_config(page_title="Employee Analytics", page_icon="📊", layout="wide")

pages = [
    st.Page("views/overview.py", title="Overview", icon="📊", default=True),
    st.Page("views/performance.py", title="Performance", icon="🏆"),
    st.Page("views/attrition.py", title="Attrition", icon="⚠️"),
    st.Page("views/bottlenecks.py", title="Bottlenecks", icon="🚧"),
    st.Page("views/employees.py", title="Employees", icon="👥"),
    st.Page("views/projects.py", title="Projects", icon="📁"),
    st.Page("views/reviews.py", title="Reviews", icon="📝"),
    st.Page("views/edit_employee.py", title="Edit employee", icon="✏️"),
]

navigation = st.navigation(pages)

with st.sidebar:
    st.subheader("System status")
    try:
        status = data.database_status()
    except ValueError as err:           # missing .env values
        st.error(f"Configuration error: {err}")
        st.stop()

    for name, is_up in status.items():
        st.write(f"{'🟢' if is_up else '🔴'} {name}")

    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

navigation.run()