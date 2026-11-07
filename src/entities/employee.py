
class Employee:

    # Constructor: initializes employee details
    def __init__(
        self,
        employee_code,
        first_name,
        last_name,
        email,
        hire_date,
        department_id,
        job_role,
        monthly_income,
        job_level=None,
        manager_id=None,
        attrition=False,
        status="Active",
        employee_id=None
    ):

        # Employee identification
        self.employee_id = employee_id
        self.employee_code = employee_code

        # Personal details
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

        # Job details
        self.hire_date = hire_date
        self.department_id = department_id
        self.job_role = job_role
        self.job_level = job_level
        self.monthly_income = monthly_income
        self.manager_id = manager_id

        # Employment status
        self.attrition = attrition
        self.status = status

    # Returns the employee's full name
    def get_full_name(self):
        return self.first_name + " " + self.last_name

    # Checks whether the employee is active
    def is_active(self):
        return self.status == "Active"

    # Checks whether the employee has left
    def has_left(self):
        return self.attrition is True

    # Validates employee information
    def validate(self):

        if not self.employee_code:
            raise ValueError("Employee code is required")

        if not self.first_name or not self.last_name:
            raise ValueError("Employee name is required")

        if not self.email or "@" not in self.email:
            raise ValueError("Enter a valid email address")

        if self.monthly_income < 0:
            raise ValueError("Monthly income cannot be negative")

        if self.department_id is None:
            raise ValueError("Department ID is required")

        return True

    # Displays employee information
    def display_details(self):

        print("Employee ID:", self.employee_id)
        print("Employee Code:", self.employee_code)
        print("Name:", self.get_full_name())
        print("Email:", self.email)
        print("Hire Date:", self.hire_date)
        print("Department ID:", self.department_id)
        print("Job Role:", self.job_role)
        print("Job Level:", self.job_level)
        print("Monthly Income:", self.monthly_income)
        print("Manager ID:", self.manager_id)
        print("Attrition:", self.attrition)
        print("Status:", self.status)
