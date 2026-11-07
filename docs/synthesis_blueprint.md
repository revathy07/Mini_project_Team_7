| Component / Attribute | Synthesis & Generation Strategy |
| --- | --- |
| **Employee Scaling (100K+)** | Sample base rows and perturb attributes (age, income, tenure, satisfaction) using source distributions. Assign unique `employee_ids` using Faker for names, emails, and genders consistent with the source. |
| **Hire Dates** | Calculated as `snapshot_date − YearsAtCompany`, incorporating random day-level jitter. |
| **Managers** | Assign a manager per department and job level, loosely matching `YearsWithCurrManager`. |
| **Projects** | Create a new reference table containing project name, department owner, start/end dates, budget, and status. |
| **Project Assignments** | Establish a many-to-many bridge table linking employees to projects with attributes for role, allocation percentage, and assigned/released dates. |
| **Review Dates & History** | Generate annual or semi-annual reviews spanning from the hire date to the snapshot date. Scores are driven by `PerformanceRating` and `JobSatisfaction` combined with noise and a trend component. |
| **Historical Department Changes** | For a subset (~10–15%), create a prior department record with an effective-date window ending at the transfer date, ensuring roles remain valid for the department. |
| **Historical Salary & Role Changes** | Back-calculate earlier salaries using `PercentSalaryHike`, `YearsSinceLastPromotion`, and `JobLevel` (with lower historical levels) to produce multiple versioned records per employee. |

Two consistency rules we’ll enforce. Without them, the history would be junk and the SCD2 queries would give wrong answers:

History windows must not overlap, and the dates must be contiguous (one version’s end date is the next one’s start date).
Everything is anchored to a fixed snapshot_date (we’ll use 2026-01-01), so runs are reproducible. We’ll also seed Faker and numpy.