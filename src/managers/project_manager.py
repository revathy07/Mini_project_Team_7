
from mysql.connector import Error

import uuid

from src.database.base_manager import BaseManager
from src.database.exceptions import ValidationError

from src.entities.project import Project
from src.entities.validation import (
    parse_date,
    validate_integer,
    validate_number,
    validate_text,
)


class ProjectManager(BaseManager):

    database_kind = "oltp"

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
            validate_integer(project_id, "Project ID", minimum=1)
            if not isinstance(updated_fields, dict):
                raise ValueError("Project updates must be provided as a mapping")
            if not updated_fields:
                raise ValueError("No project details provided for update")

            for field in updated_fields:
                if field not in self.ALLOWED_PROJECT_FIELDS:
                    raise ValueError(
                        "Updating this project field is not allowed: " + field
                    )

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM Projects WHERE project_id = %s",
                (project_id,),
            )
            current = cursor.fetchone()
            if current is None:
                raise ValueError("Project not found")
            Project(**{**current, **updated_fields}).validate()

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
            validate_integer(employee_id, "Employee ID", minimum=1)
            validate_integer(project_id, "Project ID", minimum=1)
            start = parse_date(start_date, "Assignment start date")
            planned_end = parse_date(
                planned_end_date, "Assignment planned end date", optional=True
            )
            if planned_end is not None and planned_end < start:
                raise ValueError(
                    "Assignment planned end date cannot be before start date"
                )
            validate_text(role_in_project, "Project role", 50, optional=True)
            validate_integer(
                allocation_percentage, "Allocation percentage",
                minimum=0, maximum=100, optional=True,
            )
            validate_number(
                budget, "Assignment budget", minimum=0,
                maximum=9999999999.99, optional=True, decimal_places=2,
            )
            validate_text(priority, "Assignment priority", 10, optional=True)
            if priority and priority.strip() not in {
                "Low", "Medium", "High", "Critical"
            }:
                raise ValueError(
                    "Assignment priority must be Low, Medium, High, or Critical"
                )

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
            validate_integer(assignment_id, "Assignment ID", minimum=1)
            end_date = parse_date(end_date, "Assignment end date")

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
            raise

        except Error as e:
            if connection:
                connection.rollback()
            print("Database error while releasing employee:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()
            print("Unexpected error while releasing employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
        # --------------------------------------------------
    # CREATE PROJECT (used by the UI)
    # --------------------------------------------------
    INSERT_FIELDS = (
        "project_code", "project_name", "department_id", "project_manager_id",
        "start_date", "planned_end_date", "end_date", "budget",
        "status", "priority",
    )

    def create_project(self, project):
        """Insert project and assign the next PROJ-##### code.
        Returns (project_id, project_code). All-or-nothing."""
        try:
            project.validate()
        except ValueError as err:
            raise ValidationError(str(err)) from err

        temp_code = "TMP-" + uuid.uuid4().hex[:12]
        values = [
            temp_code if field == "project_code" else getattr(project, field)
            for field in self.INSERT_FIELDS
        ]
        sql = (
            f"INSERT INTO Projects ({', '.join(self.INSERT_FIELDS)}) "
            f"VALUES ({', '.join(['%s'] * len(self.INSERT_FIELDS))})"
        )

        with self.transaction() as cursor:
            cursor.execute(sql, values)
            project_id = cursor.lastrowid
            code = f"PROJ-{project_id:05d}"
            cursor.execute(
                "UPDATE Projects SET project_code = %s WHERE project_id = %s",
                (code, project_id),
            )

        project.project_id, project.project_code = project_id, code
        return project_id, code

    # --------------------------------------------------
    # SEARCH PROJECTS
    # --------------------------------------------------
    def search_projects(self, term="", department_id=None, status=None, limit=50):
        conditions, params = [], []
        term = (term or "").strip()

        if term:
            conditions.append("(p.project_name LIKE %s OR p.project_code LIKE %s)")
            params += [f"%{term}%", f"{term}%"]
        if department_id is not None:
            conditions.append("p.department_id = %s")
            params.append(department_id)
        if status:
            conditions.append("p.status = %s")
            params.append(status)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT p.project_id, p.project_code, p.project_name,
                   d.department_name, p.status, p.priority, p.start_date,
                   p.planned_end_date, p.end_date, p.budget
            FROM Projects p
            LEFT JOIN Departments d ON d.department_id = p.department_id
            {where}
            ORDER BY p.project_id DESC
            LIMIT %s
        """
        return self.fetch_all(sql, tuple(params) + (int(limit),))
