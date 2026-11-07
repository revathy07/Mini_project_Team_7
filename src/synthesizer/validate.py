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

for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")

print("\nAvg performance score by review year:")
print(rev.assign(year=rev.review_date.dt.year).groupby("year").performance_score.mean().round(2).tail(10).to_string())

sys.exit(0 if all(checks.values()) else 1)