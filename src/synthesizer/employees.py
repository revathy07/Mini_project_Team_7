import numpy as np
import pandas as pd
from faker import Faker

from src.synthesizer.base import BaseGenerator
from src.synthesizer.config import SynthConfig


class EmployeeGenerator(BaseGenerator):
    COLUMN_MAP = {
        "EmployeeNumber": "source_employee_number",  # lineage back to the IBM row
        "Age": "age", "Attrition": "attrition", "BusinessTravel": "business_travel",
        "DistanceFromHome": "distance_from_home", "Education": "education",
        "EducationField": "education_field",
        "EnvironmentSatisfaction": "environment_satisfaction", "Gender": "gender",
        "JobInvolvement": "job_involvement", "JobLevel": "job_level",
        "JobRole": "job_role", "JobSatisfaction": "job_satisfaction",
        "MaritalStatus": "marital_status", "MonthlyIncome": "monthly_income",
        "NumCompaniesWorked": "num_companies_worked", "OverTime": "overtime",
        "PercentSalaryHike": "percent_salary_hike",
        "PerformanceRating": "performance_rating",
        "StockOptionLevel": "stock_option_level",
        "TotalWorkingYears": "total_working_years",
        "TrainingTimesLastYear": "training_times_last_year",
        "WorkLifeBalance": "work_life_balance", "YearsAtCompany": "years_at_company",
        "YearsInCurrentRole": "years_in_current_role",
        "YearsSinceLastPromotion": "years_since_last_promotion",
        "YearsWithCurrManager": "years_with_curr_manager", "Department": "department",
    }

    OUTPUT_COLUMNS = [
        "employee_id", "source_employee_number", "first_name", "last_name", "email",
        "gender", "age", "marital_status", "education", "education_field",
        "department_id", "job_role", "job_level", "monthly_income",
        "percent_salary_hike", "hire_date", "termination_date", "attrition",
        "manager_id", "business_travel", "overtime", "distance_from_home",
        "job_satisfaction", "environment_satisfaction", "work_life_balance",
        "job_involvement", "performance_rating", "stock_option_level",
        "training_times_last_year", "num_companies_worked", "total_working_years",
        "years_at_company", "years_in_current_role", "years_since_last_promotion",
        "years_with_curr_manager",
    ]

    SATISFACTION_COLS = ["job_satisfaction", "environment_satisfaction",
                         "work_life_balance", "job_involvement"]

    def __init__(self, config: SynthConfig, rng: np.random.Generator,
                 departments: pd.DataFrame, faker: Faker):
        super().__init__(config, rng)
        self.departments = departments
        self.faker = faker

    # ---------- public ----------
    def generate(self) -> pd.DataFrame:
        base = self._load_base()
        extra_n = self.config.target_employees - len(base)
        if extra_n < 0:
            raise ValueError(f"target_employees must be >= {len(base)}")

        template = base.sample(
            n=extra_n, replace=True,
            random_state=int(self.rng.integers(0, 2**31 - 1)),
        ).reset_index(drop=True)

        df = pd.concat([base, self._perturb(template)], ignore_index=True)
        df = self._enforce_consistency(df)
        df.insert(0, "employee_id", np.arange(1, len(df) + 1))  # 1..1470 = real rows
        df = self._add_identity(df)
        df = self._add_dates(df)
        df = self._assign_managers(df)
        return df[self.OUTPUT_COLUMNS]

    # ---------- steps ----------
    def _load_base(self) -> pd.DataFrame:
        raw = pd.read_csv(self.config.raw_path, encoding="utf-8-sig")
        df = raw[list(self.COLUMN_MAP)].rename(columns=self.COLUMN_MAP)
        df["attrition"] = df["attrition"].eq("Yes")
        df["overtime"] = df["overtime"].eq("Yes")
        dept_map = dict(zip(self.departments.department_name,
                            self.departments.department_id))
        df["department_id"] = df.pop("department").map(dept_map)
        return df

    def _perturb(self, df: pd.DataFrame) -> pd.DataFrame:
        """Jitter numeric fields so synthetic rows are new people, not clones."""
        n, r = len(df), self.rng
        df["age"] = (df["age"] + r.integers(-3, 4, n)).clip(18, 60)
        df["monthly_income"] = ((df["monthly_income"] * r.normal(1.0, 0.08, n))
                                .round().astype(int).clip(lower=1009))
        df["years_at_company"] = (df["years_at_company"] + r.integers(-1, 2, n)).clip(lower=0)
        df["total_working_years"] = (df["total_working_years"] + r.integers(-1, 2, n)).clip(lower=0)
        df["distance_from_home"] = (df["distance_from_home"] + r.integers(-2, 3, n)).clip(1, 29)
        for col in self.SATISFACTION_COLS:
            shift = r.choice([-1, 0, 1], size=n, p=[0.075, 0.85, 0.075])
            df[col] = (df[col] + shift).clip(1, 4)
        return df

    @staticmethod
    def _enforce_consistency(df: pd.DataFrame) -> pd.DataFrame:
        """Jitter can break logical rules; repair them top-down."""
        df["total_working_years"] = np.minimum(df["total_working_years"], df["age"] - 18)
        df["years_at_company"] = np.minimum(df["years_at_company"], df["total_working_years"])
        for col in ["years_in_current_role", "years_since_last_promotion",
                    "years_with_curr_manager"]:
            df[col] = np.minimum(df[col], df["years_at_company"])
        return df

    def _add_identity(self, df: pd.DataFrame) -> pd.DataFrame:
        f = self.faker
        df["first_name"] = [f.first_name_male() if g == "Male" else f.first_name_female()
                            for g in df["gender"]]
        df["last_name"] = [f.last_name() for _ in range(len(df))]
        df["email"] = (df["first_name"] + "." + df["last_name"] + "."
                       + df["employee_id"].astype(str) + "@company.com"
                       ).str.lower().str.replace(r"[^a-z0-9.@]", "", regex=True)
        return df

    def _add_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        snap, n = self.config.snapshot_date, len(df)
        tenure_days = df["years_at_company"].to_numpy() * 365 + self.rng.integers(0, 365, n)
        df["hire_date"] = snap - pd.to_timedelta(tenure_days, unit="D")

        # Leavers (attrition == True) get a termination date in the last year
        term = pd.Series(snap - self.random_days(1, 365, n))
        earliest = df["hire_date"] + pd.Timedelta(days=30)
        term = term.where(term > earliest, earliest).where(lambda s: s <= snap, snap)
        df["termination_date"] = term.where(df["attrition"])  # NaT for active staff
        return df

    def _assign_managers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Level 5 = executive layer (no manager); level 4 reports to level 5;
        everyone else reports to a level 4+ person in the same department."""
        mgr = np.full(len(df), np.nan)
        for _, grp in df.groupby("department_id"):
            execs = grp.index[grp["job_level"] == 5].to_numpy()
            seniors = grp.index[grp["job_level"] >= 4].to_numpy()
            l4 = grp.index[grp["job_level"] == 4].to_numpy()
            low = grp.index[grp["job_level"] < 4].to_numpy()
            if len(seniors):
                mgr[low] = df.loc[self.rng.choice(seniors, len(low)), "employee_id"].to_numpy()
            if len(execs):
                mgr[l4] = df.loc[self.rng.choice(execs, len(l4)), "employee_id"].to_numpy()
        df["manager_id"] = pd.Series(mgr).astype("Int64")
        return df