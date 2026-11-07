import pandas as pd

c = (pd.read_csv("data/processed/employee_changes.csv")
       .sort_values(["employee_id", "version_no"]).reset_index(drop=True))
t = ["department_id", "job_role", "job_level", "monthly_income"]

same = (c[t] == c[t].shift()).all(axis=1) & (c.employee_id == c.employee_id.shift())
print("duplicate versions:", int(same.sum()))
print(c[same].change_type.value_counts().to_string())

ids = c[same].employee_id.head(3)
print(c[c.employee_id.isin(ids)].to_string(index=False))