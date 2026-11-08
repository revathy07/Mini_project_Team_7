from src.managers.project_manager import ProjectManager

manager = ProjectManager()

# Release the employee from the existing assignment
manager.release_employee(
    assignment_id=141111,
    end_date="2026-05-30"
)

# Check the employee's assignments
employee_assignments = manager.get_employee_assignments(1)

print("Employee assignments:", employee_assignments)