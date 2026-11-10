| Component / Attribute | Implemented synthesis strategy |
| --- | --- |
| **Employee Scaling (100K+)** | Samples base rows and perturbs attributes (age, income, tenure, satisfaction) using source distributions. Generates unique employee IDs and uses Faker for names and emails. |
| **Hire Dates** | Calculated as `snapshot_date − YearsAtCompany`, incorporating random day-level jitter. |
| **Managers** | Assigns managers by department and job level, loosely matching `YearsWithCurrManager`. |
| **Projects** | Generates project records with project name, department owner, dates, budget, and status. |
| **Project Assignments** | Builds a many-to-many bridge table linking employees to projects, with role, allocation percentage, and assigned/released dates. |
| **Review Dates & History** | Generates annual or semi-annual reviews spanning hire date to snapshot date. Scores combine `PerformanceRating` and `JobSatisfaction` with noise and a trend component. |
| **Historical Department Changes** | Generates prior department records for a subset of employees, with effective-date windows ending at transfer dates and roles valid for the department. |
| **Historical Salary & Role Changes** | Generates earlier salary and role versions using salary hike, promotion, and job-level attributes. |

The synthesizer is implemented in `src/synthesizer/` and writes the generated
CSV files to `data/processed/`. Its default configuration uses 100,000
employees, 1,500 projects, a seed of 42, and a fixed snapshot date of
2026-01-01. The shared NumPy generator and Faker are seeded so runs with the
same inputs are reproducible.

Employee change history is generated with contiguous, non-overlapping
effective-date windows: each closed version ends when the next version starts,
and each employee has one current version. The validation script checks these
history rules along with employee, department, project, assignment, and review
relationships and date ranges:

```bash
uv run python src/synthesizer/validate.py
```

See the [ETL pipeline guide](./ETL_pipeline_guide.md) for how to load the
processed CSV files into MySQL.