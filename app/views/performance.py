import plotly.express as px
import streamlit as st

from app import data
from src.database.exceptions import DataAccessError

st.title("Performance")

try:
    min_year, max_year = data.review_year_range()
except DataAccessError as err:
    st.error(f"Could not load review years: {err}")
    st.stop()

year_from, year_to = st.slider("Review years", min_year, max_year,
                               (min_year, max_year))

# ---------- trend per department ----------
st.subheader("Year-over-year score by department")
st.caption("Each review counts in the department the employee belonged to "
           "on the review date, so transfers do not rewrite history (SCD Type 2).")
try:
    trend = data.yearly_trend_by_department(year_from, year_to)
except DataAccessError as err:
    st.error(f"Could not load trend: {err}")
    st.stop()

if trend.empty:
    st.info("No reviews in this period.")
else:
    fig = px.line(trend, x="year", y="avg_score", color="department_name",
                  markers=True, hover_data={"reviews": ":,"},
                  labels={"year": "Review year", "avg_score": "Average score (1-5)",
                          "department_name": "Department"})
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig)

# ---------- top performers ----------
st.subheader("Top performers by department")
c1, c2 = st.columns(2)
top_n = c1.slider("Top N per department", 3, 15, 5)
min_reviews = c2.slider("Minimum reviews in period", 1, 8, 3,
                        help="Avoids ranking someone on one lucky review.")
st.caption("Active employees, ranked inside each department with DENSE_RANK(). "
           "Ties share a rank, so a department can list more than N people.")

try:
    top = data.top_performers(year_from, year_to, min_reviews, top_n)
except DataAccessError as err:
    st.error(f"Could not load top performers: {err}")
    st.stop()

if top.empty:
    st.info("No employees match these filters.")
else:
    departments = list(top["department_name"].unique())
    for dept, tab in zip(departments, st.tabs(departments)):
        with tab:
            shown = top[top["department_name"] == dept].drop(columns="department_name")
            st.dataframe(
                shown.rename(columns={
                    "dept_rank": "Rank", "employee_code": "Code",
                    "full_name": "Name", "job_role": "Role",
                    "avg_score": "Avg score", "avg_goal": "Avg goal %",
                    "review_count": "Reviews"}),
                hide_index=True)