import pandas as pd

from src.synthesizer.base import BaseGenerator


class DepartmentGenerator(BaseGenerator):
    DEPARTMENTS = [
        # name, location, annual budget
        ("Sales", "New York", 4_500_000),
        ("Research & Development", "San Francisco", 9_000_000),
        ("Human Resources", "Chicago", 1_800_000),
    ]

    def generate(self) -> pd.DataFrame:
        df = pd.DataFrame(self.DEPARTMENTS,
                          columns=["department_name", "location", "annual_budget"])
        df.insert(0, "department_id", range(1, len(df) + 1))
        df["cost_center"] = [f"CC-{100 + i * 10}" for i in range(len(df))]
        return df