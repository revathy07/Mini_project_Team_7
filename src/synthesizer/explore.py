from pathlib import Path
import pandas as pd


RAW_PATH = Path(r"data\raw\IBM HR Analytics Employee Attrition & Performance.csv")

def main() -> None:
    df = pd.read_csv(RAW_PATH)

    print("=== SHAPE ===")
    print(df.shape)

    print("\n=== COLUMNS & DTYPE ===")
    print(df.dtypes.to_string())
    
    print("\n=== NULL COUNTS (Total) ===")
    print(int(df.isnull().sum().sum()))
    
    print("\n=== CONSTANT COLUMNS (1 unique value) ===")
    constants = [c for c in df.columns if df[c].nunique() == 1]
    print(constants)
    
    print("\n=== EmployeeNumber UNIQUE ? ===")
    print(df["EmployeeNumber"].is_unique)
    
    print("\n=== CATEGORICAL COLUMNS ===")
    for col in df.select_dtypes(include=["object","str"]).columns:
        print(f"\n", df[col].value_counts().to_string())
    
    
    print("\n=== NUMERIC SUMMARY ===")
    print(df[["Age", "MonthlyIncome", "TotalWorkingYears", "YearsAtCompany",
              "YearsInCurrentRole", "YearsSinceLastPromotion",
              "PercentSalaryHike"]].describe().round(1).to_string())

    print("\n--- Consistency checks (we rely on these for history) ---")
    print("YearsInCurrentRole > YearsAtCompany:", (df.YearsInCurrentRole > df.YearsAtCompany).sum())
    print("YearsSinceLastPromotion > YearsAtCompany:", (df.YearsSinceLastPromotion > df.YearsAtCompany).sum())
    print("YearsAtCompany > TotalWorkingYears:", (df.YearsAtCompany > df.TotalWorkingYears).sum())

    print("\n--- Salary by JobLevel ---")
    print(df.groupby("JobLevel")["MonthlyIncome"].agg(["min", "median", "max"]).to_string())

    print("\n--- Department x JobRole ---")
    print(pd.crosstab(df.JobRole, df.Department).to_string())
    

if __name__ == "__main__":
    main()