
from mysql.connector import Error
import uuid

from src.database.base_manager import BaseManager
from src.database.exceptions import ValidationError
from src.entities.employee import Employee


class EmployeeManager(BaseManager):

    database_kind = "oltp"

    # Fields that are allowed to be updated
    ALLOWED_UPDATE_FIELDS = {
        "first_name",
        "last_name",
        "email",
        "gender",
        "age",
        "hire_date",
        "termination_date",
        "department_id",
        "job_role",
        "job_level",
        "monthly_income",
        "percent_salary_hike",
        "manager_id",
        "attrition",
        "status",
        "overtime",
        "business_travel",
        "distance_from_home",
        "job_satisfaction",
        "environment_satisfaction",
        "work_life_balance",
        "job_involvement",
        "total_working_years"
    }

    # --------------------------------------------------
    # 1. ADD EMPLOYEE
    # --------------------------------------------------
    def add_employee(self, employee):

        connection = None
        cursor = None

        try:
            # Validate employee details before insertion
            employee.validate()

            # Establish database connection
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            # SQL query to insert employee details
            query = """
                INSERT INTO Employees (
                    employee_code,
                    first_name,
                    last_name,
                    email,
                    gender,
                    age,
                    hire_date,
                    termination_date,
                    department_id,
                    job_role,
                    job_level,
                    monthly_income,
                    percent_salary_hike,
                    manager_id,
                    attrition,
                    status,
                    overtime,
                    business_travel,
                    distance_from_home,
                    job_satisfaction,
                    environment_satisfaction,
                    work_life_balance,
                    job_involvement,
                    total_working_years
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            values = (
                employee.employee_code,
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.gender,
                employee.age,
                employee.hire_date,
                employee.termination_date,
                employee.department_id,
                employee.job_role,
                employee.job_level,
                employee.monthly_income,
                employee.percent_salary_hike,
                employee.manager_id,
                employee.attrition,
                employee.status,
                employee.overtime,
                employee.business_travel,
                employee.distance_from_home,
                employee.job_satisfaction,
                employee.environment_satisfaction,
                employee.work_life_balance,
                employee.job_involvement,
                employee.total_working_years
            )

            # Execute the insertion query
            cursor.execute(query, values)

            # Save changes
            connection.commit()

            # Store the generated employee ID in the object
            employee.employee_id = cursor.lastrowid

            print("Employee added successfully.")

            return employee.employee_id

        except ValueError as e:
            print("Employee validation failed:", e)
            raise

        except Error as e:
            if connection:
                connection.rollback()

            print("Database error while adding employee:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()

            print("Unexpected error while adding employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 2. GET EMPLOYEE BY ID
    # --------------------------------------------------
    def get_employee_by_id(self, employee_id):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)

            # Dictionary cursor returns column names with values
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Employees
                WHERE employee_id = %s
            """

            cursor.execute(query, (employee_id,))

            result = cursor.fetchone()

            if result is None:
                print("Employee not found.")
                return None

            # Convert database record into an Employee object
            employee = Employee(**result)

            return employee

        except Error as e:
            print("Database error while retrieving employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 3. GET EMPLOYEE BY CODE
    # --------------------------------------------------
    def get_employee_by_code(self, employee_code):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Employees
                WHERE employee_code = %s
            """

            cursor.execute(query, (employee_code,))

            result = cursor.fetchone()

            if result is None:
                print("Employee not found.")
                return None

            employee = Employee(**result)

            return employee

        except Error as e:
            print("Database error while retrieving employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 4. GET ALL EMPLOYEES
    # --------------------------------------------------
    def get_all_employees(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Employees
                ORDER BY employee_id
            """

            cursor.execute(query)

            results = cursor.fetchall()

            # Convert every database record into an Employee object
            employees = []

            for row in results:
                employee = Employee(**row)
                employees.append(employee)

            return employees

        except Error as e:
            print("Database error while retrieving employees:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 5. UPDATE EMPLOYEE
    # --------------------------------------------------
    def update_employee(self, employee_id, updated_fields):

        connection = None
        cursor = None

        try:
            if not updated_fields:
                raise ValueError("No employee details provided for update")

            # Check whether all requested fields are permitted
            for field in updated_fields:

                if field not in self.ALLOWED_UPDATE_FIELDS:
                    raise ValueError(
                        "Updating this employee field is not allowed: "
                        + field
                    )

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            # Build the SET portion of the SQL query
            set_clause = ", ".join(
                [f"{field} = %s" for field in updated_fields]
            )

            query = f"""
                UPDATE Employees
                SET {set_clause}
                WHERE employee_id = %s
            """

            # Get the values in the same order as the fields
            values = tuple(updated_fields.values()) + (employee_id,)

            cursor.execute(query, values)

            if cursor.rowcount == 0:
                # Check whether the employee exists
                cursor.execute(
                    "SELECT employee_id FROM Employees WHERE employee_id = %s",
                    (employee_id,)
                )

                if cursor.fetchone() is None:
                    raise ValueError("Employee not found")

            connection.commit()

            print("Employee updated successfully.")

            return True

        except (ValueError, Error) as e:
            if connection:
                connection.rollback()

            print("Error while updating employee:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()

            print("Unexpected error while updating employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 6. DELETE EMPLOYEE
    # --------------------------------------------------
    def delete_employee(self, employee_id):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                DELETE FROM Employees
                WHERE employee_id = %s
            """

            cursor.execute(query, (employee_id,))

            if cursor.rowcount == 0:
                raise ValueError("Employee not found")

            connection.commit()

            print("Employee deleted successfully.")

            return True

        except (ValueError, Error) as e:
            if connection:
                connection.rollback()

            print("Error while deleting employee:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()

            print("Unexpected error while deleting employee:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()
        # --------------------------------------------------
    # 7. CREATE EMPLOYEE (used by the UI)
    # --------------------------------------------------
    INSERT_FIELDS = (
        "employee_code", "first_name", "last_name", "email", "gender", "age",
        "hire_date", "termination_date", "department_id", "job_role",
        "job_level", "monthly_income", "percent_salary_hike", "manager_id",
        "attrition", "status", "overtime", "business_travel",
        "distance_from_home", "job_satisfaction", "environment_satisfaction",
        "work_life_balance", "job_involvement", "total_working_years",
    )

    def create_employee(self, employee):
        """Insert employee and assign the next EMP-###### code.
        Returns (employee_id, employee_code). All-or-nothing."""
        try:
            employee.validate()
        except ValueError as err:
            raise ValidationError(str(err)) from err

        temp_code = "TMP-" + uuid.uuid4().hex[:12]
        values = [
            temp_code if field == "employee_code" else getattr(employee, field)
            for field in self.INSERT_FIELDS
        ]
        sql = (
            f"INSERT INTO Employees ({', '.join(self.INSERT_FIELDS)}) "
            f"VALUES ({', '.join(['%s'] * len(self.INSERT_FIELDS))})"
        )

        with self.transaction() as cursor:
            cursor.execute(sql, values)
            employee_id = cursor.lastrowid
            code = f"EMP-{employee_id:06d}"
            cursor.execute(
                "UPDATE Employees SET employee_code = %s WHERE employee_id = %s",
                (code, employee_id),
            )

        employee.employee_id, employee.employee_code = employee_id, code
        return employee_id, code

    # --------------------------------------------------
    # 8. SEARCH (paged, never loads all 100K rows)
    # --------------------------------------------------
    def search_employees(self, term="", department_id=None,
                         active_only=True, limit=50, offset=0):
        conditions, params = [], []
        term = (term or "").strip()

        if term:
            conditions.append(
                "(e.employee_code LIKE %s OR e.email LIKE %s "
                "OR CONCAT(e.first_name, ' ', e.last_name) LIKE %s)"
            )
            params += [f"{term}%", f"{term}%", f"%{term}%"]
        if department_id is not None:
            conditions.append("e.department_id = %s")
            params.append(department_id)
        if active_only:
            conditions.append("e.termination_date IS NULL")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT e.employee_id, e.employee_code,
                   CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                   e.email, d.department_name, e.job_role, e.job_level,
                   e.monthly_income, e.hire_date, e.status
            FROM Employees e
            JOIN Departments d ON d.department_id = e.department_id
            {where}
            ORDER BY e.employee_id DESC
            LIMIT %s OFFSET %s
        """
        return self.fetch_all(sql, tuple(params) + (int(limit), int(offset)))

    # --------------------------------------------------
    # 9. LOOKUPS FOR FORM DROPDOWNS
    # --------------------------------------------------
    def list_departments(self):
        return self.fetch_all(
            "SELECT department_id, department_name FROM Departments "
            "ORDER BY department_name"
        )

    def list_job_roles(self, department_id):
        rows = self.fetch_all(
            "SELECT DISTINCT job_role FROM Employees "
            "WHERE department_id = %s ORDER BY job_role",
            (department_id,),
        )
        return [row["job_role"] for row in rows]

    def list_managers(self, department_id, limit=200):
        """Active level 4+ staff in the department."""
        return self.fetch_all(
            "SELECT employee_id, "
            "CONCAT(first_name, ' ', last_name, ' (', employee_code, ')') AS label "
            "FROM Employees "
            "WHERE department_id = %s AND job_level >= 4 AND termination_date IS NULL "
            "ORDER BY job_level DESC, last_name, first_name LIMIT %s",
            (department_id, int(limit)),
        )