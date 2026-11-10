from datetime import date

import streamlit as st

from app import data
from app.iam import can, current_user
from src.database.exceptions import DataAccessError

st.title("Performance reviews")
user = current_user()
can_submit = can(user, "submit_reviews")

# ---------- manual sync (also the retry path) ----------
if can(user, "sync_warehouse"):
    with st.expander("Warehouse sync"):
        st.caption("A saved review reaches the dashboards after a sync. This runs "
                   "automatically on submit. Use the button to retry if it failed.")
        if st.button("Sync reviews to warehouse now"):
            try:
                data.sync_reviews()
            except DataAccessError as err:
                st.error(str(err))
            else:
                st.success("Warehouse is up to date.")

# ---------- pick employee ----------
term = st.text_input("Find employee (name, code or email, at least 2 characters)",
                     key="rev_term")
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
                           format_func=choices.get)

try:
    summary = data.employee_summary(employee_id)
    history = data.employee_review_history(employee_id)
except DataAccessError as err:
    st.error(f"Could not load employee: {err}")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Department", summary["department_name"])
c2.metric("Role", summary["job_role"])
c3.metric("Hired", str(summary["hire_date"]))
st.caption(f"Reviewer: {summary['manager_name'] or 'none (no manager on record)'}")

st.markdown("**Recent reviews**")
if history.empty:
    st.caption("No reviews yet.")
else:
    st.dataframe(history.rename(columns={
        "review_date": "Date", "review_period": "Cycle",
        "performance_score": "Score", "performance_rating": "Rating",
        "goal_achievement_pct": "Goal %", "peer_feedback_score": "Peer",
        "promotion_recommended": "Promotion?"}), hide_index=True)

if summary["hire_date"] > date.today():
    st.warning("Hire date is in the future. No review can be recorded yet.")
    st.stop()

# ---------- form (keyed by employee so defaults reset on change) ----------
with st.form(f"submit_review_{employee_id}"):
    f1, f2 = st.columns(2)
    review_date = f1.date_input("Review date", value=date.today(),
                                min_value=summary["hire_date"],
                                max_value=date.today())
    cycle = f2.selectbox("Cycle", ["Annual", "Mid-Year"])

    score = st.slider("Performance score", 1.0, 5.0, 3.0, 0.05,
                      help="Rating (1-5) is derived by rounding the score.")
    f3, f4 = st.columns(2)
    goal = f3.number_input("Goal achievement %", min_value=0.0, max_value=130.0,
                           value=80.0, step=1.0)
    peer = f4.slider("Peer feedback score", 1.0, 5.0, 3.0, 0.05)
    promotion = st.checkbox("Recommend for promotion")
    comments = st.text_area("Comments (optional)")

    submitted = st.form_submit_button(
        "Submit review", disabled=not can_submit
    )

if submitted and can_submit:
    try:
        result = data.submit_review(
            employee_id=employee_id,
            reviewer_id=summary["manager_id"],
            review_date=review_date,
            review_period=f"{review_date.year}-{cycle}",
            performance_score=round(float(score), 2),
            goal_achievement_pct=round(float(goal), 1),
            peer_feedback_score=round(float(peer), 2),
            promotion_recommended=promotion,
            comments=comments.strip() or None,
        )
    except DataAccessError as err:
        st.error(str(err))
    else:
        st.success(f"Review {result['review_id']} saved.")
        if result["synced"]:
            st.success("Warehouse updated. Dashboards include this review.")
        else:
            st.warning(result["warning"])