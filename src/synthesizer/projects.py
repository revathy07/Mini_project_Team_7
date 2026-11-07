import numpy as np
import pandas as pd

from src.synthesizer.base import BaseGenerator
from src.synthesizer.config import SynthConfig


class ProjectGenerator(BaseGenerator):
    ADJECTIVES = ["Apex", "Blue", "Crimson", "Delta", "Eagle", "Falcon", "Granite",
                  "Horizon", "Iron", "Jade", "Kestrel", "Lunar", "Nova", "Orion",
                  "Phoenix", "Quartz", "Raven", "Summit", "Titan", "Vertex"]
    NOUNS = ["Migration", "Platform", "Rollout", "Audit", "Portal", "Pipeline",
             "Upgrade", "Initiative", "Expansion", "Overhaul", "Pilot", "Launch"]

    def __init__(self, config: SynthConfig, rng: np.random.Generator,
                 departments: pd.DataFrame):
        super().__init__(config, rng)
        self.departments = departments

    def generate(self) -> pd.DataFrame:
        n, r, snap = self.config.num_projects, self.rng, self.config.snapshot_date

        # Bigger-budget departments own more projects
        weights = self.departments.annual_budget / self.departments.annual_budget.sum()
        dept_ids = r.choice(self.departments.department_id, n, p=weights)

        start = snap - self.random_days(30, 365 * 12, n)
        planned_end = start + self.random_days(90, 900, n)
        delay = np.clip(r.normal(15, 35, n).astype(int), -20, 150)  # schedule slippage
        actual_end = planned_end + pd.to_timedelta(delay, unit="D")
        is_active = np.asarray(actual_end > snap)

        roll = r.random(n)
        status = np.select(
            [~is_active & (roll < 0.08), ~is_active, is_active & (roll < 0.08)],
            ["Cancelled", "Completed", "On Hold"],
            default="Active",
        )

        adj, noun = r.choice(self.ADJECTIVES, n), r.choice(self.NOUNS, n)
        df = pd.DataFrame({
            "project_id": np.arange(1, n + 1),
            "project_name": [f"{a} {b} {i:04d}" for i, (a, b) in enumerate(zip(adj, noun), 1)],
            "department_id": dept_ids,
            "start_date": start,
            "planned_end_date": planned_end,
            "end_date": pd.Series(actual_end).where(~is_active),  # NaT while still running
            "budget": (r.lognormal(12.5, 0.6, n) / 1000).round().astype(int) * 1000,
            "status": status,
            "priority": r.choice(["Low", "Medium", "High", "Critical"], n,
                                 p=[0.2, 0.45, 0.25, 0.1]),
        })
        return df