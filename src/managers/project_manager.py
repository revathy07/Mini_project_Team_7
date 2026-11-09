
from mysql.connector import Error
from datetime import datetime
from src.database.db_manager import DatabaseConnection
from src.entities.project import Project


class ProjectManager(DatabaseConnection):

    # Fields allowed to be updated in the Projects table
    ALLOWED_PROJECT_FIELDS = {
        "project_code",
        "project_name",
        "department_id",
        "project_manager_id",
        "start_date",
        "planned_end_date",
        "end_date",
        "budget",
        "status",
        "priority"
    }

    def __init__(self):
        super().__init__()
        self.database_name = "employee_oltp"

    # --------------------------------------------------
    # 1. ADD PROJECT
    # --------------------------------------------------
    def add_project(self, project):
        connection = None
        cursor = None

        try:
            project.validate()

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                INSERT INTO Projects (
                    project_code, project_name, department_id,
                    project_manager_id, start_date, planned_end_date,
                    end_date, budget, status, priority
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                project.project_code,
                project.project_name,
                project.department_id,
                project.project_manager_id,
                project.start_date,
                project.planned_end_date,
                project.end_date,
                project.budget,
                project.status,
                project.priority
            )

            cursor.execute(query, values)
            connection.commit()

            project.project_id = cursor.lastrowid
            print("Project added successfully.")

            return project.project_id

        except ValueError as e:
            print("Project validation failed:", e)
            raise

        except Error as e:
            if connection:
                connection.rollback()
            print("Database error while adding project:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()
            print("Unexpected error while adding project:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 2. GET PROJECT BY ID
    # --------------------------------------------------
    def get_project_by_id(self, project_id):
        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Projects
                WHERE project_id = %s
            """

            cursor.execute(query, (project_id,))
            result = cursor.fetchone()

            if result is None:
                print("Project not found.")
                return None

            return Project(**result)

        except Error as e:
            print("Database error while retrieving project:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 3. GET ALL PROJECTS
    # --------------------------------------------------
    def get_all_projects(self):
        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Projects
                ORDER BY project_id
            """

            cursor.execute(query)
            results = cursor.fetchall()

            projects = []

            for row in results:
                project = Project(**row)
                projects.append(project)

            return projects

        except Error as e:
            print("Database error while retrieving projects:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 4. UPDATE PROJECT
    # --------------------------------------------------
    def update_project(self, project_id, updated_fields):
        connection = None
        cursor = None

        try:
            if not updated_fields:
                raise ValueError("No project details provided for update")

            for field in updated_fields:
                if field not in self.ALLOWED_PROJECT_FIELDS:
                    raise ValueError(
                        "Updating this project field is not allowed: " + field
                    )

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            set_clause = ", ".join(
                [f"{field} = %s" for field in updated_fields]
            )

            query = f"""
                UPDATE Projects
                SET {set_clause}
                WHERE project_id = %s
            """

            values = tuple(updated_fields.values()) + (project_id,)

            cursor.execute(query, values)

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT project_id FROM Projects WHERE project_id = %s",
                    (project_id,)
                )

                if cursor.fetchone() is None:
                    raise ValueError("Project not found")

            connection.commit()

            print("Project updated successfully.")
            return True

        except (ValueError, Error) as e:
            if connection:
                connection.rollback()
            print("Error while updating project:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()
            print("Unexpected error while updating project:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 5. DELETE PROJECT
    # --------------------------------------------------
    def delete_project(self, project_id):
        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                DELETE FROM Projects
                WHERE project_id = %s
            """

            cursor.execute(query, (project_id,))

            if cursor.rowcount == 0:
                raise ValueError("Project not found")

            connection.commit()

            print("Project deleted successfully.")
            return True

        except (ValueError, Error) as e:
            if connection:
                connection.rollback()
            print("Error while deleting project:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()
            print("Unexpected error while deleting project:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 6. ASSIGN EMPLOYEE TO PROJECT
    # --------------------------------------------------
    def assign_employee(
        self,
        employee_id,
        project_id,
        start_date,
        role_in_project=None,
        allocation_percentage=None,
        planned_end_date=None,
        budget=None,
        priority=None
    ):
        connection = None
        cursor = None

        try:
            if employee_id is None:
                raise ValueError("Employee ID is required")

            if project_id is None:
                raise ValueError("Project ID is required")

            if not start_date:
                raise ValueError("Assignment start date is required")

            if allocation_percentage is not None and allocation_percentage < 0:
                raise ValueError("Allocation percentage cannot be negative")

            if budget is not None and budget < 0:
                raise ValueError("Assignment budget cannot be negative")

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                INSERT INTO Project_Assignments (
                    employee_id,
                    project_id,
                    role_in_project,
                    allocation_percentage,
                    start_date,
                    planned_end_date,
                    budget,
                    priority,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active')
            """

            values = (
                employee_id,
                project_id,
                role_in_project,
                allocation_percentage,
                start_date,
                planned_end_date,
                budget,
                priority
            )

            cursor.execute(query, values)
            connection.commit()

            assignment_id = cursor.lastrowid

            print("Employee assigned to project successfully.")
            return assignment_id

        except ValueError as e:
            print("Assignment validation failed:", e)
            raise

        except Error as e:
            if connection:
                connection.rollback()
            print("Database error while assigning employee:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()
            print("Unexpected error while assigning employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 7. GET PROJECT ASSIGNMENTS
    # --------------------------------------------------
    def get_project_assignments(self, project_id):
        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    pa.*,
                    e.employee_code,
                    e.first_name,
                    e.last_name,
                    p.project_name
                FROM Project_Assignments pa
                JOIN Employees e
                    ON pa.employee_id = e.employee_id
                JOIN Projects p
                    ON pa.project_id = p.project_id
                WHERE pa.project_id = %s
                ORDER BY pa.start_date
            """

            cursor.execute(query, (project_id,))
            return cursor.fetchall()

        except Error as e:
            print("Database error while retrieving assignments:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 8. GET EMPLOYEE ASSIGNMENTS
    # --------------------------------------------------
    def get_employee_assignments(self, employee_id):
        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    pa.*,
                    p.project_code,
                    p.project_name
                FROM Project_Assignments pa
                JOIN Projects p
                    ON pa.project_id = p.project_id
                WHERE pa.employee_id = %s
                ORDER BY pa.start_date
            """

            cursor.execute(query, (employee_id,))
            return cursor.fetchall()

        except Error as e:
            print("Database error while retrieving employee assignments:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 9. RELEASE EMPLOYEE FROM PROJECT
    # --------------------------------------------------
    def release_employee(self, assignment_id, end_date):
        connection = None
        cursor = None

        try:
            # Convert string date into Python date object
            if isinstance(end_date, str):
                end_date = datetime.strptime(
                    end_date, "%Y-%m-%d"
                ).date()

            # Connect to the OLTP database
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            # Retrieve assignment start date
            query = """
                SELECT start_date, status
                FROM Project_Assignments
                WHERE assignment_id = %s
            """

            cursor.execute(query, (assignment_id,))
            assignment = cursor.fetchone()

            if assignment is None:
                raise ValueError("Assignment not found")

            start_date = assignment["start_date"]

            # Validate release date
            if end_date < start_date:
                raise ValueError(
                    "End date cannot be before assignment start date"
                )

            if assignment["status"] == "Completed":
                raise ValueError("Employee has already been released")

            # Update assignment status and end date
            update_query = """
                UPDATE Project_Assignments
                SET end_date = %s,
                    status = 'Completed'
                WHERE assignment_id = %s
            """

            cursor.execute(update_query, (end_date, assignment_id))
            connection.commit()

            print("Employee released from project successfully.")
            return True

        except ValueError as e:
            if connection:
                connection.rollback()
            print("Validation error:", e)
            return False

        except Error as e:
            if connection:
                connection.rollback()
            print("Database error while releasing employee:", e)
            return False

        except Exception as e:
            if connection:
                connection.rollback()
            print("Unexpected error while releasing employee:", e)
            return False

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
