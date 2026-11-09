
from mysql.connector import Error

from src.database.db_manager import DatabaseConnection
from src.entities.employee import Employee


class EmployeeManager(DatabaseConnection):

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

    def __init__(self):
        # Initialize the parent DatabaseConnection class
        super().__init__()

        # Use the OLTP database for employee operations
        self.database_name = "employee_oltp"

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
