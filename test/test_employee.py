from src.entities.employee import Employee

employee = Employee(
    employee_code="EMP1001",
    first_name="John",
    last_name="Smith",
    email="john@example.com",
    hire_date="2024-01-15",
    department_id=1,
    job_role="Data Analyst",
    monthly_income=50000,
    age=25
)

print(employee.get_full_name())
print(employee.is_active())
print(employee.has_left())
print(employee.validate())

employee.display_details()