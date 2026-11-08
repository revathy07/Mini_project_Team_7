
from src.managers.employee_manager import EmployeeManager
from src.entities.employee import Employee


# Create EmployeeManager object
manager = EmployeeManager()


# Test 1: Add employee
employee = Employee(
    employee_code="TEST1001",
    first_name="John",
    last_name="Smith",
    email="john.test1001@example.com",
    hire_date="2026-01-15",
    department_id=1,
    job_role="Data Analyst",
    monthly_income=50000,
    age=25
)

employee_id = manager.add_employee(employee)

print("Generated Employee ID:", employee_id)


# Test 2: Retrieve employee
retrieved_employee = manager.get_employee_by_id(employee_id)

if retrieved_employee:
    retrieved_employee.display_details()


# Test 3: Update employee
manager.update_employee(
    employee_id,
    {
        "job_role": "Senior Data Analyst",
        "monthly_income": 60000
    }
)


# Test 4: Retrieve all employees
employees = manager.get_all_employees()

print("Total employees:", len(employees))


# Test 5: Delete test employee
manager.delete_employee(employee_id)
