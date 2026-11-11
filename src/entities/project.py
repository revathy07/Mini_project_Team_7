
from src.entities.validation import (
    parse_date,
    validate_integer,
    validate_number,
    validate_text,
)


class Project:

    # Constructor: initializes project details
    def __init__(
        self,
        project_code,
        project_name,
        start_date,
        department_id=None,
        planned_end_date=None,
        end_date=None,
        budget=None,
        project_manager_id=None,
        status="Active",
        priority=None,
        project_id=None
    ):

        # Project identification
        self.project_id = project_id
        self.project_code = project_code
        self.project_name = project_name

        # Project ownership
        self.department_id = department_id
        self.project_manager_id = project_manager_id

        # Project duration
        self.start_date = start_date
        self.planned_end_date = planned_end_date
        self.end_date = end_date

        # Budget and priority
        self.budget = budget
        self.priority = priority

        # Project status
        self.status = status

    # Checks whether the project is active
    def is_active(self):
        return self.status == "Active"

    # Checks whether the project has been completed
    def is_completed(self):
        return self.status == "Completed"

    # Checks whether the project is delayed
    def is_delayed(self):
        return (
            self.planned_end_date is not None
            and self.end_date is not None
            and self.end_date > self.planned_end_date
        )

    # Validates project information
    def validate(self):
        validate_text(self.project_code, "Project code", 20)
        validate_text(self.project_name, "Project name", 150)
        start = parse_date(self.start_date, "Project start date")
        planned_end = parse_date(
            self.planned_end_date, "Planned end date", optional=True
        )
        end = parse_date(self.end_date, "Project end date", optional=True)
        validate_integer(self.project_id, "Project ID", minimum=1, optional=True)
        validate_integer(
            self.department_id, "Department ID", minimum=1, optional=True
        )
        validate_integer(
            self.project_manager_id, "Project manager ID",
            minimum=1, optional=True,
        )
        validate_number(
            self.budget, "Project budget", minimum=0, maximum=9999999999.99,
            optional=True, decimal_places=2,
        )
        validate_text(self.status, "Project status", 20)
        if self.status not in {"Active", "On Hold", "Completed", "Cancelled"}:
            raise ValueError("Project status must be Active, On Hold, Completed, or Cancelled")
        validate_text(self.priority, "Project priority", 10, optional=True)
        if self.priority and self.priority.strip() not in {
            "Low", "Medium", "High", "Critical"
        }:
            raise ValueError("Project priority must be Low, Medium, High, or Critical")

        if planned_end is not None and planned_end < start:
            raise ValueError("Planned end date cannot be before start date")
        if end is not None and end < start:
            raise ValueError("End date cannot be before start date")

        return True

    # Displays project details
    def display_details(self):

        print("\n----- Project Details -----")
        print("Project ID:", self.project_id)
        print("Project Code:", self.project_code)
        print("Project Name:", self.project_name)
        print("Department ID:", self.department_id)
        print("Project Manager ID:", self.project_manager_id)
        print("Start Date:", self.start_date)
        print("Planned End Date:", self.planned_end_date)
        print("Actual End Date:", self.end_date)
        print("Budget:", self.budget)
        print("Priority:", self.priority)
        print("Status:", self.status)
        print("Delayed:", self.is_delayed())
