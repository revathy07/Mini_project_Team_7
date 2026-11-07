import argparse

import numpy as np
import pandas as pd
from faker import Faker

from src.synthesizer.assignments import AssignmentGenerator
from src.synthesizer.config import SynthConfig
from src.synthesizer.departments import DepartmentGenerator
from src.synthesizer.employees import EmployeeGenerator
from src.synthesizer.projects import ProjectGenerator
from src.synthesizer.reviews import ReviewGenerator

from src.synthesizer.changes import ChangeGenerator

class SynthesisPipeline:
    def __init__(self, config: SynthConfig):
        self.config = config

    def run(self) -> dict[str, pd.DataFrame]:
        cfg = self.config
        rng = np.random.default_rng(cfg.seed)
        Faker.seed(cfg.seed)
        faker = Faker()

        departments = DepartmentGenerator(cfg, rng).generate()
        employees = EmployeeGenerator(cfg, rng, departments, faker).generate()
        projects = ProjectGenerator(cfg, rng, departments).generate()
        assignments = AssignmentGenerator(cfg, rng, employees, projects).generate()
        reviews = ReviewGenerator(cfg, rng, employees).generate()
        changes = ChangeGenerator(cfg, rng, employees, departments).generate()

        tables = {
            "departments": departments,
            "employees": employees,
            "projects": projects,
            "project_assignments": assignments,
            "performance_reviews": reviews,
            "performance_reviews": reviews,
            "employee_changes": changes,
        }
        self._save(tables)
        return tables

    def _save(self, tables: dict[str, pd.DataFrame]) -> None:
        self.config.out_dir.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            df = df.copy()
            for col in df.select_dtypes(bool).columns:  # MySQL-friendly 0/1
                df[col] = df[col].astype(int)
            path = self.config.out_dir / f"{name}.csv"
            df.to_csv(path, index=False, date_format="%Y-%m-%d")
            print(f"{name + '.csv':28s} {len(df):>9,} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic HR data")
    parser.add_argument("--employees", type=int, default=100_000)
    parser.add_argument("--projects", type=int, default=1_500)
    args = parser.parse_args()
    SynthesisPipeline(SynthConfig(target_employees=args.employees,
                                  num_projects=args.projects)).run()