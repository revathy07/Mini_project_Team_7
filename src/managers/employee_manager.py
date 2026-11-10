
from mysql.connector import Error
import uuid

from src.database.base_manager import BaseManager

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from src.database.exceptions import NotFoundError, ValidationError

from src.entities.employee import Employee


def classify_change(old, new):
    """Name the business event behind a change.
    old/new: dicts with department_id, job_role, job_level, monthly_income."""
    if old["department_id"] != new["department_id"]:
        return "Department Transfer"
    old_level, new_level = old["job_level"] or 0, new["job_level"] or 0
    if new_level > old_level:
        return "Promotion"
    if new_level < old_level:
        return "Demotion"
    if old["monthly_income"] != new["monthly_income"]:
        return ("Salary Increase" if new["monthly_income"] > old["monthly_income"]
                else "Salary Adjustment")
    if old["job_role"] != new["job_role"]:
        return "Role Change"
    return None

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
    
    # --------------------------------------------------
    # 10. ONE-ROW SUMMARY (form headers, default reviewer)
    # --------------------------------------------------
    def get_employee_summary(self, employee_id):
        return self.fetch_one("""
            SELECT e.employee_id, e.employee_code,
                   CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                   d.department_name, e.job_role, e.hire_date, e.termination_date,
                   e.manager_id,
                   CONCAT(m.first_name, ' ', m.last_name) AS manager_name
            FROM Employees e
            JOIN Departments d ON d.department_id = e.department_id
            LEFT JOIN Employees m ON m.employee_id = e.manager_id
            WHERE e.employee_id = %s
        """, (employee_id,))
    
        # --------------------------------------------------
    # 11. JOB CHANGE WITH CHANGE LOG (SCD2 source of truth in OLTP)
    # --------------------------------------------------
    TRACKED_FIELDS = ("department_id", "job_role", "job_level", "monthly_income")

    @staticmethod
    def _floor_from(hire_date, *event_dates):
        """Earliest allowed effective date: hire date, or the day after the
        latest review / assignment (those warehouse facts already point to the
        current version, so a change must not be dated before them)."""
        floor = hire_date
        for event in event_dates:
            if event is not None and event + timedelta(days=1) > floor:
                floor = event + timedelta(days=1)
        return floor

    def get_change_floor(self, employee_id):
        row = self.fetch_one("""
            SELECT e.hire_date,
                   (SELECT MAX(r.review_date) FROM Performance_Reviews r
                     WHERE r.employee_id = e.employee_id) AS last_review,
                   (SELECT MAX(a.start_date) FROM Project_Assignments a
                     WHERE a.employee_id = e.employee_id) AS last_assignment
            FROM Employees e WHERE e.employee_id = %s
        """, (employee_id,))
        if row is None:
            raise NotFoundError("Employee not found.")
        return self._floor_from(row["hire_date"], row["last_review"],
                                row["last_assignment"])

    def get_employee_for_edit(self, employee_id):
        return self.fetch_one("""
            SELECT e.employee_id, e.employee_code,
                   CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                   e.department_id, d.department_name, e.job_role, e.job_level,
                   e.monthly_income, e.hire_date, e.termination_date, e.manager_id,
                   CONCAT(m.first_name, ' ', m.last_name) AS manager_name
            FROM Employees e
            JOIN Departments d ON d.department_id = e.department_id
            LEFT JOIN Employees m ON m.employee_id = e.manager_id
            WHERE e.employee_id = %s
        """, (employee_id,))

    def update_job_details(self, employee_id, changes, effective_date):
        """Apply department / role / level / income (and optional manager_id)
        changes. Updates Employees and writes Employee_Change_Log in ONE
        transaction. Returns {"change_type", "diffs", "manager_changed"}.
        The warehouse is NOT touched here (see WarehouseSync)."""
        allowed = set(self.TRACKED_FIELDS) | {"manager_id"}
        if not changes or set(changes) - allowed:
            raise ValidationError("Nothing to change, or an unsupported field was sent.")
        if not isinstance(effective_date, date):
            raise ValidationError("Effective date must be a valid date.")
        if effective_date > date.today():
            raise ValidationError("Effective date cannot be in the future.")

        with self.transaction(dictionary=True) as cursor:
            cursor.execute("""
                SELECT e.department_id, d.department_name, e.job_role, e.job_level,
                       e.monthly_income, e.hire_date, e.termination_date, e.manager_id,
                       (SELECT MAX(r.review_date) FROM Performance_Reviews r
                         WHERE r.employee_id = e.employee_id) AS last_review,
                       (SELECT MAX(a.start_date) FROM Project_Assignments a
                         WHERE a.employee_id = e.employee_id) AS last_assignment
                FROM Employees e
                JOIN Departments d ON d.department_id = e.department_id
                WHERE e.employee_id = %s
                FOR UPDATE
            """, (employee_id,))
            old = cursor.fetchone()
            if old is None:
                raise NotFoundError("Employee not found.")
            if old["termination_date"] is not None:
                raise ValidationError(
                    "This employee has left the company; job details cannot be changed.")

            # ---- new values, coerced and validated ----
            new = {field: old[field] for field in self.TRACKED_FIELDS}
            try:
                if "department_id" in changes:
                    new["department_id"] = int(changes["department_id"])
                if "job_role" in changes:
                    new["job_role"] = str(changes["job_role"]).strip()
                if "job_level" in changes:
                    new["job_level"] = int(changes["job_level"])
                if "monthly_income" in changes:
                    new["monthly_income"] = Decimal(
                        str(changes["monthly_income"])).quantize(Decimal("0.01"))
            except (TypeError, ValueError, InvalidOperation):
                raise ValidationError("A changed value is not valid.")

            if not new["job_role"]:
                raise ValidationError("Job role is required.")
            if not 1 <= new["job_level"] <= 5:
                raise ValidationError("Job level must be between 1 and 5.")
            if new["monthly_income"] <= 0:
                raise ValidationError("Monthly income must be greater than zero.")

            new_dept_name = old["department_name"]
            if new["department_id"] != old["department_id"]:
                cursor.execute(
                    "SELECT department_name FROM Departments WHERE department_id = %s",
                    (new["department_id"],))
                row = cursor.fetchone()
                if row is None:
                    raise ValidationError("Department not found.")
                new_dept_name = row["department_name"]

            if ((new["department_id"], new["job_role"])
                    != (old["department_id"], old["job_role"])):
                cursor.execute(
                    "SELECT 1 AS ok FROM Employees "
                    "WHERE department_id = %s AND job_role = %s LIMIT 1",
                    (new["department_id"], new["job_role"]))
                if cursor.fetchone() is None:
                    raise ValidationError(
                        f"Role '{new['job_role']}' does not exist in {new_dept_name}.")

            # ---- what actually changed ----
            pairs = [
                ("department", old["department_name"], new_dept_name,
                 new["department_id"] != old["department_id"]),
                ("job_role", old["job_role"], new["job_role"],
                 new["job_role"] != old["job_role"]),
                ("job_level", old["job_level"], new["job_level"],
                 new["job_level"] != old["job_level"]),
                ("monthly_income", old["monthly_income"], new["monthly_income"],
                 new["monthly_income"] != old["monthly_income"]),
            ]
            diffs = [(name, str(o), str(n)) for name, o, n, changed in pairs if changed]

            manager_changed = ("manager_id" in changes
                               and changes["manager_id"] != old["manager_id"])
            if not diffs and not manager_changed:
                raise ValidationError("No changes to save.")

            if diffs:
                floor = self._floor_from(old["hire_date"], old["last_review"],
                                         old["last_assignment"])
                if effective_date < floor:
                    raise ValidationError(
                        f"Effective date cannot be before {floor} (hire date, or the "
                        "day after the latest review or project assignment).")

            if manager_changed and changes["manager_id"] is not None:
                if changes["manager_id"] == employee_id:
                    raise ValidationError("An employee cannot be their own manager.")
                cursor.execute(
                    "SELECT 1 AS ok FROM Employees "
                    "WHERE employee_id = %s AND termination_date IS NULL",
                    (changes["manager_id"],))
                if cursor.fetchone() is None:
                    raise ValidationError("Chosen manager not found or has left.")

            # ---- write ----
            sets, params = [], []
            for field in self.TRACKED_FIELDS:
                if new[field] != old[field]:
                    sets.append(f"{field} = %s")
                    params.append(new[field])
            if manager_changed:
                sets.append("manager_id = %s")
                params.append(changes["manager_id"])
            cursor.execute(
                f"UPDATE Employees SET {', '.join(sets)} WHERE employee_id = %s",
                (*params, employee_id))

            change_type = classify_change(old, new) if diffs else None
            for field_name, old_value, new_value in diffs:
                cursor.execute(
                    "INSERT INTO Employee_Change_Log "
                    "(employee_id, change_date, change_type, field_name, old_value, new_value) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (employee_id, effective_date, change_type,
                     field_name, old_value, new_value))

        return {"change_type": change_type, "diffs": diffs,
                "manager_changed": manager_changed}