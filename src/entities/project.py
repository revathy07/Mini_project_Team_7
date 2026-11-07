
class Project:

    # Constructor: initializes project details
    def __init__(
        self,
        project_code,
        project_name,
        department_id,
        start_date,
        end_date=None,
        project_manager_id=None,
        status="Active",
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
        self.end_date = end_date

        # Project status
        self.status = status

    # Checks whether the project is active
    def is_active(self):
        return self.status == "Active"

    # Checks whether the project has been completed
    def is_completed(self):
        return self.status == "Completed"

    # Validates project information
    def validate(self):

        if not self.project_code:
            raise ValueError("Project code is required")

        if not self.project_name:
            raise ValueError("Project name is required")

        if self.department_id is None:
            raise ValueError("Department ID is required")

        if not self.start_date:
            raise ValueError("Project start date is required")

        return True

    # Displays project details
    def display_details(self):

        print("Project ID:", self.project_id)
        print("Project Code:", self.project_code)
        print("Project Name:", self.project_name)
        print("Department ID:", self.department_id)
        print("Project Manager ID:", self.project_manager_id)
        print("Start Date:", self.start_date)
        print("End Date:", self.end_date)
        print("Status:", self.status)
