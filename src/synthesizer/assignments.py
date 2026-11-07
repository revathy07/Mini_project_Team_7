import numpy as np
import pandas as pd

from src.synthesizer.base import BaseGenerator
from src.synthesizer.config import SynthConfig


class AssignmentGenerator(BaseGenerator):
    ROLES = ["Contributor", "Lead", "Analyst", "Reviewer", "Coordinator", "Sponsor"]

    def __init__(self, config: SynthConfig, rng: np.random.Generator,
                 employees: pd.DataFrame, projects: pd.DataFrame):
        super().__init__(config, rng)
        self.employees = employees
        self.projects = projects.reset_index(drop=True)

    def generate(self) -> pd.DataFrame:
        r, snap = self.rng, self.config.snapshot_date
        emp = self.employees[["employee_id", "department_id", "hire_date", "termination_date"]]

        # 0-5 attempted assignments per employee; invalid/overlapping ones get filtered
        counts = r.choice([0, 1, 2, 3, 4, 5], size=len(emp),
                          p=[0.05, 0.25, 0.30, 0.20, 0.12, 0.08])
        a = emp.iloc[np.repeat(np.arange(len(emp)), counts)].reset_index(drop=True)
        n = len(a)

        # 85% of the time pick a project owned by the employee's own department
        chosen = r.integers(0, len(self.projects), n)
        same_dept = r.random(n) < 0.85
        for dept_id, grp in self.projects.groupby("department_id"):
            mask = same_dept & (a["department_id"].to_numpy() == dept_id)
            chosen[mask] = r.choice(grp.index.to_numpy(), mask.sum())
        p = self.projects.iloc[chosen].reset_index(drop=True)

        # Assignment window = overlap of employee tenure and project life
        start = (pd.concat([p["start_date"], a["hire_date"]], axis=1).max(axis=1)
                 + self.random_days(0, 14, n))
        end_cap = pd.concat([p["end_date"].fillna(snap),
                             a["termination_date"].fillna(snap)], axis=1).min(axis=1)
        keep = (end_cap - start).dt.days >= 14

        release = end_cap - self.random_days(0, 7, n)
        still_open = p["end_date"].isna() & a["termination_date"].isna()
        release = release.where(~still_open)  # NaT = currently assigned

        out = pd.DataFrame({
            "employee_id": a["employee_id"],
            "project_id": p["project_id"],
            "role": r.choice(self.ROLES, n),
            "allocation_pct": r.choice([10, 20, 25, 50, 75, 100], n,
                                       p=[0.10, 0.15, 0.20, 0.30, 0.15, 0.10]),
            "assigned_date": start,
            "released_date": release,
        })
        out = (out[keep].drop_duplicates(["employee_id", "project_id"])
               .reset_index(drop=True))
        out.insert(0, "assignment_id", np.arange(1, len(out) + 1))
        return out