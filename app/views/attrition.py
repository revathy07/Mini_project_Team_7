import plotly.express as px
import streamlit as st

from app import data
from src.database.exceptions import DataAccessError

FACTOR_ORDER = {
    "Overtime": ["No", "Yes"],
    "Business travel": ["Non-Travel", "Travel_Rarely", "Travel_Frequently"],
    "Job satisfaction": ["Low (1-2)", "High (3-4)"],
    "Tenure": ["0-1 yrs", "2-4 yrs", "5-9 yrs", "10+ yrs"],
    "Income quartile (within level)": ["Q1", "Q2", "Q3", "Q4"],
}

st.title("Attrition risk")

try:
    dept_map = data.departments()
except DataAccessError as err:
    st.error(f"Could not load departments: {err}")
    st.stop()

dept_id = st.selectbox(
    "Department", options=[None, *dept_map],
    format_func=lambda d: "All departments" if d is None else dept_map[d])

try:
    factors = data.attrition_by_factor(dept_id)
    distribution = data.risk_distribution(dept_id)
    at_risk = data.high_risk_employees(dept_id, 25)
except DataAccessError as err:
    st.error(f"Could not load attrition data: {err}")
    st.stop()

# ---------- attrition rate by factor ----------
tenure = factors[factors["factor"] == "Tenure"]
total = tenure["headcount"].sum()
baseline = 100 * tenure["leavers"].sum() / total if total else 0

c1, c2 = st.columns(2)
c1.metric("Employees in scope", f"{int(total):,}")
c2.metric("Overall attrition rate", f"{baseline:.1f}%")

st.subheader("Who leaves more often?")
st.caption("Attrition rate = leavers / headcount in each group. "
           "Dotted line = company average.")

items = list(FACTOR_ORDER.items())
for i in range(0, len(items), 2):
    cols = st.columns(2)
    for col, (factor, order) in zip(cols, items[i:i + 2]):
        sub = factors[factors["factor"] == factor]
        with col:
            st.markdown(f"**{factor}**")
            if sub.empty:
                st.info("No data.")
                continue
            fig = px.bar(sub, x="bucket", y="attrition_rate", text_auto=".1f",
                         category_orders={"bucket": order},
                         hover_data={"headcount": ":,", "leavers": ":,"},
                         labels={"bucket": "", "attrition_rate": "Attrition %"})
            fig.add_hline(y=baseline, line_dash="dot")
            st.plotly_chart(fig)

# ---------- current risk ----------
st.subheader("Current employees at risk")
st.caption("Rule-based score, one point each: overtime, job satisfaction 1-2, "
           "work-life balance 1-2, frequent travel, commute over 20 km, "
           "lowest pay quartile for the level, under 2 years tenure. "
           "A heuristic for prioritising conversations, not a trained model. "
           "Missing survey answers (new hires) count as no risk.")

left, right = st.columns([2, 3])
with left:
    if distribution.empty:
        st.info("No active employees.")
    else:
        fig = px.bar(distribution, x="risk_score", y="employees", text_auto=",",
                     labels={"risk_score": "Risk score (0-7)", "employees": "Active employees"})
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig)
with right:
    st.markdown("**Highest scores**")
    st.dataframe(
        at_risk.rename(columns={
            "employee_code": "Code", "full_name": "Name",
            "department_name": "Department", "job_role": "Role",
            "risk_score": "Score", "risk_factors": "Why"}),
        hide_index=True)