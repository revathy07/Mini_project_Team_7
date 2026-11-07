from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SynthConfig:
    seed: int = 42
    target_employees: int = 100_000
    num_projects: int = 1_500
    max_reviews_per_employee: int = 8
    snapshot_date: pd.Timestamp = pd.Timestamp("2026-01-01")
    raw_path: Path = Path(r"data\raw\IBM HR Analytics Employee Attrition & Performance.csv")
    out_dir: Path = Path("data/processed")