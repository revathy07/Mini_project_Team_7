import numpy as np
import pandas as pd

from src.synthesizer.base import BaseGenerator
from src.synthesizer.config import SynthConfig


class ReviewGenerator(BaseGenerator):
    def __init__(self, config: SynthConfig, rng: np.random.Generator,
                 employees: pd.DataFrame):
        super().__init__(config, rng)
        self.employees = employees.reset_index(drop=True)

    def generate(self) -> pd.DataFrame:
        r, snap = self.rng, self.config.snapshot_date
        e = self.employees
        end = e["termination_date"].fillna(snap)

        # How many annual reviews each employee has had (capped)
        full_years = ((end - e["hire_date"]).dt.days // 365).clip(lower=0).to_numpy()
        n_rev = np.minimum(full_years, self.config.max_reviews_per_employee)
        idx = np.repeat(np.arange(len(e)), n_rev)
        m = len(idx)

        # Anniversary number k for each review row (the most recent n_rev anniversaries)
        group_start = np.cumsum(n_rev) - n_rev
        pos = np.arange(m) - np.repeat(group_start, n_rev)
        k = (full_years - n_rev + 1)[idx] + pos

        base = e.iloc[idx].reset_index(drop=True)
        review_date = (base["hire_date"]
                       + pd.to_timedelta(k * 365 + r.integers(0, 31, m), unit="D"))
        keep = (review_date <= end.iloc[idx].reset_index(drop=True)).to_numpy()

        # ---- score model ----
        ability = (3.2
                   + 0.6 * (e["performance_rating"] - 3)
                   + 0.15 * (e["job_satisfaction"] - 2.5)
                   + 0.10 * (e["job_involvement"] - 2.5)).to_numpy()
        emp_effect = r.normal(0, 0.35, len(e))   # persistent per-person offset
        slope = r.normal(0.04, 0.08, len(e))     # per-person improving/declining trend

        year = review_date.dt.year.to_numpy()
        years = np.arange(year.min(), year.max() + 1)
        year_effect = r.normal(0, 0.08, len(years))
        year_effect[years == 2020] -= 0.20       # a company-wide dip to find in the dashboard
        
        score = (ability[idx] + emp_effect[idx]
                 + slope[idx] * (year - self.config.snapshot_date.year)
                 + year_effect[year - year.min()]
                 + r.normal(0, 0.25, m))
        score = np.clip(score, 1, 5).round(2)

        out = pd.DataFrame({
            "employee_id": base["employee_id"],
            "reviewer_id": base["manager_id"],
            "review_date": review_date,
            "review_cycle": pd.Series(year).astype(str) + "-Annual",
            "performance_score": score,
            "performance_rating": np.clip(np.rint(score), 1, 5).astype(int),
            "goal_achievement_pct": np.clip(40 + 14 * score + r.normal(0, 8, m), 0, 130).round(1),
            "peer_feedback_score": np.clip(score + r.normal(0, 0.4, m), 1, 5).round(2),
            "promotion_recommended": (score >= 4.2) & (r.random(m) < 0.5),
        })
        out = out[keep].reset_index(drop=True)
        out.insert(0, "review_id", np.arange(1, len(out) + 1))
        return out