
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

        if not self.project_code:
            raise ValueError("Project code is required")

        if not self.project_name:
            raise ValueError("Project name is required")

        if not self.start_date:
            raise ValueError("Project start date is required")

        if self.budget is not None and self.budget < 0:
            raise ValueError("Project budget cannot be negative")

        if (
            self.planned_end_date is not None
            and self.planned_end_date < self.start_date
        ):
            raise ValueError("Planned end date cannot be before start date")

        if self.end_date is not None and self.end_date < self.start_date:
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
