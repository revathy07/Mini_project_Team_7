import re

from src.entities.validation import (
    parse_date,
    validate_boolean,
    validate_integer,
    validate_number,
    validate_text,
)

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
    
    @staticmethod
    def _as_date(value):
        """Accept date, datetime or 'YYYY-MM-DD' text. Return a date, or None."""
        try:
            return parse_date(value, "Date")
        except ValueError:
            return None

    # Validates employee information
    def validate(self):
        validate_text(self.employee_code, "Employee code", 20)
        validate_text(self.first_name, "First name", 50)
        validate_text(self.last_name, "Last name", 50)
        if (not isinstance(self.email, str)
                or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email)
                or len(self.email) > 100):
            raise ValueError("Enter a valid email address")

        validate_number(
            self.monthly_income, "Monthly income", minimum=0.01,
            maximum=9999999999.99, decimal_places=2,
        )
        validate_text(self.job_role, "Job role", 50)
        hire = parse_date(self.hire_date, "Hire date")
        term = parse_date(
            self.termination_date, "Termination date", optional=True
        )
        if term is not None and term < hire:
            raise ValueError("Termination date cannot be before hire date")
        validate_integer(self.department_id, "Department ID", minimum=1)
        validate_integer(self.employee_id, "Employee ID", minimum=1, optional=True)
        validate_integer(self.manager_id, "Manager ID", minimum=1, optional=True)
        validate_integer(self.age, "Age", minimum=18, maximum=70, optional=True)
        validate_integer(
            self.job_level, "Job level", minimum=1, maximum=5, optional=True
        )
        validate_integer(
            self.percent_salary_hike, "Percent salary hike",
            minimum=0, maximum=100, optional=True,
        )
        validate_integer(
            self.distance_from_home, "Distance from home",
            minimum=0, maximum=100, optional=True,
        )
        validate_integer(
            self.total_working_years, "Total working years",
            minimum=0, maximum=100, optional=True,
        )
        if (self.total_working_years is not None and self.age is not None
                and self.total_working_years > self.age - 18):
            raise ValueError("Total working years cannot exceed age minus 18")

        for label, value in (
            ("Job satisfaction", self.job_satisfaction),
            ("Environment satisfaction", self.environment_satisfaction),
            ("Work-life balance", self.work_life_balance),
            ("Job involvement", self.job_involvement),
        ):
            validate_integer(value, label, minimum=1, maximum=4, optional=True)

        validate_text(self.gender, "Gender", 10, optional=True)
        if self.gender and self.gender.strip() not in {
            "Male", "Female"
        }:
            raise ValueError("Gender must be Male or Female")
        validate_text(self.status, "Employment status", 20)
        if self.status not in {"Active", "Terminated"}:
            raise ValueError("Employment status must be Active or Terminated")
        validate_text(self.business_travel, "Business travel", 20, optional=True)
        if self.business_travel and self.business_travel.strip() not in {
            "Non-Travel", "Travel_Rarely", "Travel_Frequently"
        }:
            raise ValueError(
                "Business travel must be Non-Travel, Travel_Rarely, or Travel_Frequently"
            )
        if (
            self.employee_id is not None
            and self.manager_id == self.employee_id
        ):
            raise ValueError("An employee cannot be their own manager")
        validate_boolean(self.attrition, "Attrition")
        validate_boolean(self.overtime, "Overtime", optional=True)

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
