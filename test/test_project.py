from src.entities.project import Project

project = Project(
    project_code="PRJ101",
    project_name="Employee Analytics",
    start_date="2026-01-01",
    planned_end_date="2026-06-01",
    end_date="2026-06-15",
    department_id=1,
    budget=500000,
    priority="High"
)

print(project.is_active())
print(project.is_completed())
print(project.is_delayed())
print(project.validate())

project.display_details()