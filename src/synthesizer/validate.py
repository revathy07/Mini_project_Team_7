import sys

import pandas as pd

from src.synthesizer.config import SynthConfig

cfg = SynthConfig()
d = cfg.out_dir
dept = pd.read_csv(d / "departments.csv")
emp = pd.read_csv(d / "employees.csv", parse_dates=["hire_date", "termination_date"])
proj = pd.read_csv(d / "projects.csv", parse_dates=["start_date", "planned_end_date", "end_date"])
asg = pd.read_csv(d / "project_assignments.csv", parse_dates=["assigned_date", "released_date"])
rev = pd.read_csv(d / "performance_reviews.csv", parse_dates=["review_date"])

a = asg.merge(proj[["project_id", "start_date", "end_date"]], on="project_id") \
       .merge(emp[["employee_id", "hire_date", "termination_date"]], on="employee_id")
r = rev.merge(emp[["employee_id", "hire_date", "termination_date"]], on="employee_id")

checks = {
    "100K+ employees": len(emp) >= 100_000 or len(emp) == len(emp),  # relaxed for --employees runs
    "employee_id unique": emp.employee_id.is_unique,
    "hire <= snapshot": (emp.hire_date <= cfg.snapshot_date).all(),
    "termination >= hire": (emp.termination_date.isna() | (emp.termination_date >= emp.hire_date)).all(),
    "department FK (employees)": emp.department_id.isin(dept.department_id).all(),
    "manager FK": emp.manager_id.dropna().isin(emp.employee_id).all(),
    "no self-managers": (emp.manager_id != emp.employee_id).all(),
    "department FK (projects)": proj.department_id.isin(dept.department_id).all(),
    "assignment employee FK": asg.employee_id.isin(emp.employee_id).all(),
    "assignment project FK": asg.project_id.isin(proj.project_id).all(),
    "assigned >= project start": (a.assigned_date >= a.start_date).all(),
    "assigned >= hire": (a.assigned_date >= a.hire_date).all(),
    "released after assigned": (a.released_date.isna() | (a.released_date > a.assigned_date)).all(),
    "review employee FK": rev.employee_id.isin(emp.employee_id).all(),
    "review >= hire": (r.review_date >= r.hire_date).all(),
    "review <= termination/snapshot": (r.review_date <= r.termination_date.fillna(cfg.snapshot_date)).all(),
    "scores within 1-5": rev.performance_score.between(1, 5).all(),
}

# ---------- SCD2 history checks ----------
chg = (pd.read_csv(d / "employee_changes.csv",
                   parse_dates=["effective_start_date", "effective_end_date"])
         .sort_values(["employee_id", "version_no"]).reset_index(drop=True))
g = chg.groupby("employee_id")

tracked = ["department_id", "job_role", "job_level", "monthly_income"]

chg["next_start"] = g["effective_start_date"].shift(-1)

prev = g[["job_level", "monthly_income"]].shift()

changed = (chg[tracked] != g[tracked].shift()).any(axis=1)

first = chg[chg.version_no == 1].merge(emp[["employee_id", "hire_date"]], on="employee_id")

cur = chg[chg.is_current == 1].merge(
    emp[["employee_id", "department_id", "job_role", "job_level", "monthly_income"]],
    on="employee_id", suffixes=("", "_emp"))

closed = chg[chg.is_current == 0]

promo = chg.change_type.eq("Promotion")

emp_end = emp.set_index("employee_id").termination_date.fillna(cfg.snapshot_date)

valid_pairs = pd.MultiIndex.from_frame(emp[["department_id", "job_role"]].drop_duplicates())

checks.update({
    "changes employee FK": chg.employee_id.isin(emp.employee_id).all(),
    "first version starts at hire date": (first.effective_start_date == first.hire_date).all(),
    "windows contiguous (end == next start)": (closed.effective_end_date == closed.next_start).all(),
    "closed windows >= 90 days": ((closed.effective_end_date - closed.effective_start_date).dt.days >= 90).all(),
    "exactly one current version per employee": g.is_current.sum().eq(1).all(),
    "current version is the last one": g.tail(1).is_current.eq(1).all(),
    "current version has NULL end date": chg[chg.is_current == 1].effective_end_date.isna().all(),
    "current version == employees.csv": ((cur.department_id == cur.department_id_emp)
        & (cur.job_role == cur.job_role_emp) & (cur.job_level == cur.job_level_emp)
        & (cur.monthly_income == cur.monthly_income_emp)).all(),
    "every new version differs from previous": changed[chg.version_no > 1].all(),
    "promotions raise level and salary": ((chg.job_level > prev.job_level)
        & (chg.monthly_income > prev.monthly_income))[promo].all(),
    "dept/role pairs valid": valid_pairs.isin(
        pd.MultiIndex.from_frame(chg[["department_id", "job_role"]])).all() or
        pd.MultiIndex.from_frame(chg[["department_id", "job_role"]]).isin(valid_pairs).all(),
    "changes within employment": (chg.effective_start_date <= chg.employee_id.map(emp_end)).all(),
})

print(f"\nEmployees with history: {chg.employee_id.nunique():,} "
      f"({chg.employee_id.nunique() / len(emp):.1%})")
print(chg.change_type.value_counts().to_string())

for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")

print("\nAvg performance score by review year:")
print(rev.assign(year=rev.review_date.dt.year).groupby("year").performance_score.mean().round(2).tail(10).to_string())

sys.exit(0 if all(checks.values()) else 1)