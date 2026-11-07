import numpy as np
import pandas as pd

from src.synthesizer.base import BaseGenerator
from src.synthesizer.config import SynthConfig


class ChangeGenerator(BaseGenerator):
    """Builds employee_changes.csv: the full version history (SCD Type 2 source)
    for a subset of employees, by walking each current state backwards
    through 1-3 business events."""

    MIN_GAP_DAYS = 90          # min gap: hire->1st change, between changes, last change->end
    MAX_CHANGES = 3
    CHANGE_COUNT_P = [0.60, 0.22, 0.12, 0.06]   # P(0, 1, 2, 3 changes)
    EVENT_TYPES = np.array(["Promotion", "Salary Increase", "Department Transfer"])
    EVENT_CUM_P = np.cumsum([0.35, 0.45, 0.20])
    MIN_SALARY = 1000          # IBM minimum is 1009, so history can always go lower

    COLUMNS = ["employee_id", "version_no", "change_type", "department_id",
               "job_role", "job_level", "monthly_income",
               "effective_start_date", "effective_end_date", "is_current"]

    def __init__(self, config: SynthConfig, rng: np.random.Generator,
                 employees: pd.DataFrame, departments: pd.DataFrame):
        super().__init__(config, rng)
        self.employees = employees.reset_index(drop=True)
        self.dept_ids = sorted(int(d) for d in departments["department_id"])

        # Which roles really exist per department (and per dept+level) in the data
        e = self.employees
        self.roles_by_dept = {int(k): list(v) for k, v in
                              e.groupby("department_id")["job_role"].unique().items()}
        self.roles_by_dept_level = {(int(k[0]), int(k[1])): list(v) for k, v in
                                    e.groupby(["department_id", "job_level"])["job_role"].unique().items()}

    # ---------- public ----------
    def generate(self) -> pd.DataFrame:
        e, gap = self.employees, self.MIN_GAP_DAYS
        end = e["termination_date"].fillna(self.config.snapshot_date)
        tenure = (end - e["hire_date"]).dt.days.to_numpy()

        # Number of changes per employee, capped by how many fit in their tenure
        max_k = np.clip((tenure - 181) // gap + 1, 0, self.MAX_CHANGES)
        k = np.minimum(self.rng.choice(self.MAX_CHANGES + 1, size=len(e),
                                       p=self.CHANGE_COUNT_P), max_k)

        # Pre-draw all randomness (fast + reproducible): type, salary, dept, role
        draws = self.rng.random((int(k.sum()), 4))

        emp_id = e["employee_id"].to_numpy()
        hire = e["hire_date"].values.astype("datetime64[D]")
        dept = e["department_id"].to_numpy()
        role = e["job_role"].to_numpy()
        level = e["job_level"].to_numpy()
        salary = e["monthly_income"].to_numpy()
        hike = e["percent_salary_hike"].to_numpy()

        rows, ptr = [], 0
        for i in np.flatnonzero(k):
            n = int(k[i])
            ev = draws[ptr:ptr + n]
            ptr += n

            # n sorted change dates, each >= gap days apart and inside the window
            # [hire + gap, end - gap]
            span = tenure[i] - 2 * gap - (n - 1) * gap
            offs = np.sort(self.rng.integers(0, span + 1, n)) + np.arange(n) * gap
            dates = hire[i] + np.timedelta64(gap, "D") + offs.astype("timedelta64[D]")

            # Walk backwards from the current state, newest -> oldest
            states = [(int(dept[i]), role[i], int(level[i]), int(salary[i]))]
            types = [None] * n
            for j in range(n - 1, -1, -1):
                prev, kind = self._step_back(states[-1], ev[j], hike[i])
                states.append(prev)
                types[j] = kind
            states.reverse()  # oldest -> newest

            starts = [hire[i], *dates]
            ends = [*dates, pd.NaT]
            for v, (st, s, en) in enumerate(zip(states, starts, ends)):
                rows.append((emp_id[i], v + 1, "Hire" if v == 0 else types[v - 1],
                             *st, s, en, v == n))

        df = pd.DataFrame(rows, columns=self.COLUMNS)
        for col in ["effective_start_date", "effective_end_date"]:
            df[col] = pd.to_datetime(df[col])
        df.insert(0, "change_id", np.arange(1, len(df) + 1))
        return df

    # ---------- reverse one business event ----------
    def _step_back(self, state, u, hike_pct):
        """Return (state before the event, event type)."""
        dept, role, level, salary = state
        kind = int(np.searchsorted(self.EVENT_CUM_P, u[0]))
        if kind == 0 and level <= 1:        # can't have been promoted into level 1
            kind = 1

        if kind == 0:                        # Promotion
            level, salary = level - 1, salary / (1.10 + 0.20 * u[1])
        elif kind == 1:                      # Salary Increase
            salary = salary / (1 + hike_pct * (0.4 + 0.6 * u[1]) / 100)
        else:                                # Department Transfer
            others = [d for d in self.dept_ids if d != dept]
            dept = others[int(u[2] * len(others))]
            roles = self.roles_by_dept_level.get((dept, level), self.roles_by_dept[dept])
            role = roles[int(u[3] * len(roles))]
            salary = salary * (0.92 + 0.16 * u[1])

        salary = max(self.MIN_SALARY, int(round(salary)))
        if kind in (0, 1):                      # promotion / raise must lower the earlier salary
            salary = min(salary, state[3] - 1)
        return (dept, role, level, salary), self.EVENT_TYPES[kind]