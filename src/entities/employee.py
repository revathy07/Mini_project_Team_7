
class Employee:

    # Constructor: initializes employee details
    def __init__(
        self,
        employee_code,
        first_name,
        last_name,
        email,
        hire_date,
        job_role,
        monthly_income,
        employee_id=None,
        gender=None,
        age=None,
        termination_date=None,
        department_id=None,
        job_level=None,
        percent_salary_hike=None,
        manager_id=None,
        attrition=False,
        status="Active",
        overtime=None,
        business_travel=None,
        distance_from_home=None,
        job_satisfaction=None,
        environment_satisfaction=None,
        work_life_balance=None,
        job_involvement=None,

        total_working_years=None,
        updated_at=None
    ):

        # Employee identification
        self.employee_id = employee_id
        self.employee_code = employee_code

        # Personal details
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.gender = gender
        self.age = age

        # Employment dates
        self.hire_date = hire_date
        self.termination_date = termination_date

        # Job details
        self.department_id = department_id
        self.job_role = job_role
        self.job_level = job_level
        self.monthly_income = monthly_income
        self.percent_salary_hike = percent_salary_hike
        self.manager_id = manager_id

        # Employment status
        self.attrition = attrition
        self.status = status

        # Work-related details
        self.overtime = overtime
        self.business_travel = business_travel
        self.distance_from_home = distance_from_home

        # Employee satisfaction details
        self.job_satisfaction = job_satisfaction
        self.environment_satisfaction = environment_satisfaction
        self.work_life_balance = work_life_balance
        self.job_involvement = job_involvement

        # Experience
        self.total_working_years = total_working_years
        self.updated_at = updated_at

    # Returns the employee's full name
    def get_full_name(self):
        return self.first_name + " " + self.last_name

    # Checks whether the employee is active
    def is_active(self):
        return self.status == "Active"

    # Checks whether the employee has left
    def has_left(self):
        return bool(self.attrition) or self.termination_date is not None

    # Validates employee information
    def validate(self):

        if not self.employee_code:
            raise ValueError("Employee code is required")

        if not self.first_name or not self.last_name:
            raise ValueError("Employee name is required")

        if not self.email or "@" not in self.email:
            raise ValueError("Enter a valid email address")

        if not isinstance(self.monthly_income, (int, float)):
            raise ValueError("Monthly income must be numeric")

        if self.monthly_income < 0:
            raise ValueError("Monthly income cannot be negative")

        if not self.job_role:
            raise ValueError("Job role is required")

        if not self.hire_date:
            raise ValueError("Hire date is required")

        if self.age is not None and self.age <= 0:
            raise ValueError("Age must be positive")

        if self.department_id is None:
            raise ValueError("Department ID is required")

        return True

    # Displays employee information
    def display_details(self):

        print("\n----- Employee Details -----")
        print("Employee ID:", self.employee_id)
        print("Employee Code:", self.employee_code)
        print("Name:", self.get_full_name())
        print("Email:", self.email)
        print("Gender:", self.gender)
        print("Age:", self.age)
        print("Hire Date:", self.hire_date)
        print("Termination Date:", self.termination_date)
        print("Department ID:", self.department_id)
        print("Job Role:", self.job_role)
        print("Job Level:", self.job_level)
        print("Monthly Income:", self.monthly_income)
        print("Manager ID:", self.manager_id)
        print("Attrition:", self.attrition)
        print("Status:", self.status)
        print("Overtime:", self.overtime)
        print("Business Travel:", self.business_travel)
        print("Distance From Home:", self.distance_from_home)
        print("Job Satisfaction:", self.job_satisfaction)
        print("Environment Satisfaction:", self.environment_satisfaction)
        print("Work Life Balance:", self.work_life_balance)
        print("Job Involvement:", self.job_involvement)
        print("Total Working Years:", self.total_working_years)
        print("Percent Salary Hike:", self.percent_salary_hike)
        print("Updated At:", self.updated_at)
