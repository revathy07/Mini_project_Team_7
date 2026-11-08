
from mysql.connector import Error
from src.database.db_manager import DatabaseConnection


class AnalyticsManager(DatabaseConnection):

    def __init__(self):
        super().__init__()
        self.database_name = "employee_dw"

    # --------------------------------------------------
    # 1. GET CURRENT EMPLOYEE HEADCOUNT
    # --------------------------------------------------
    def get_total_employees(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                SELECT COUNT(*)
                FROM Dim_Employee
                WHERE is_current = 1
            """

            cursor.execute(query)
            result = cursor.fetchone()

            return result[0]

        except Error as e:
            print("Error retrieving employee count:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 2. GET DEPARTMENT-WISE EMPLOYEE COUNT
    # --------------------------------------------------
    def get_department_distribution(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    department_name,
                    COUNT(*) AS employee_count
                FROM Dim_Employee
                WHERE is_current = 1
                GROUP BY department_name
                ORDER BY employee_count DESC
            """

            cursor.execute(query)

            return cursor.fetchall()

        except Error as e:
            print("Error retrieving department distribution:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 3. GET ATTRITION STATISTICS
    # --------------------------------------------------
    def get_attrition_statistics(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    COUNT(*) AS total_employees,
                    SUM(CASE
                        WHEN attrition_flag = 1 THEN 1
                        ELSE 0
                    END) AS employees_left,
                    SUM(CASE
                        WHEN attrition_flag = 0 THEN 1
                        ELSE 0
                    END) AS active_employees,
                    ROUND(
                        100.0 * SUM(
                            CASE WHEN attrition_flag = 1 THEN 1 ELSE 0 END
                        ) / NULLIF(COUNT(*), 0),
                        2
                    ) AS attrition_rate
                FROM Dim_Employee
                WHERE is_current = 1
            """

            cursor.execute(query)

            return cursor.fetchone()

        except Error as e:
            print("Error retrieving attrition statistics:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 4. GET AVERAGE PERFORMANCE SCORE
    # --------------------------------------------------
    def get_average_performance(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    ROUND(AVG(performance_score), 2)
                    AS average_performance_score,

                    ROUND(AVG(performance_rating), 2)
                    AS average_performance_rating,

                    ROUND(AVG(goal_achievement_pct), 2)
                    AS average_goal_achievement,

                    COUNT(*) AS total_reviews

                FROM Fact_PerformanceReviews
            """

            cursor.execute(query)

            return cursor.fetchone()

        except Error as e:
            print("Error retrieving performance statistics:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 5. GET DEPARTMENT-WISE PERFORMANCE
    # --------------------------------------------------
    def get_department_performance(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    d.department_name,

                    ROUND(AVG(f.performance_score), 2)
                    AS average_performance,

                    ROUND(AVG(f.goal_achievement_pct), 2)
                    AS average_goal_achievement,

                    COUNT(f.review_sk) AS total_reviews

                FROM Fact_PerformanceReviews f

                JOIN Dim_Department d
                    ON f.department_sk = d.department_sk

                GROUP BY d.department_sk, d.department_name

                ORDER BY average_performance DESC
            """

            cursor.execute(query)

            return cursor.fetchall()

        except Error as e:
            print("Error retrieving department performance:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 6. GET YEAR-WISE PERFORMANCE TREND
    # --------------------------------------------------
    def get_yearly_performance_trend(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    d.year,

                    ROUND(AVG(f.performance_score), 2)
                    AS average_performance,

                    ROUND(AVG(f.performance_rating), 2)
                    AS average_rating,

                    COUNT(f.review_sk) AS total_reviews

                FROM Fact_PerformanceReviews f

                JOIN Dim_Date d
                    ON f.date_key = d.date_key

                GROUP BY d.year

                ORDER BY d.year
            """

            cursor.execute(query)

            return cursor.fetchall()

        except Error as e:
            print("Error retrieving yearly performance trend:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 7. GET PROJECT STATUS DISTRIBUTION
    # --------------------------------------------------
    def get_project_status_distribution(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    status,
                    COUNT(*) AS project_count

                FROM Dim_Project

                GROUP BY status

                ORDER BY project_count DESC
            """

            cursor.execute(query)

            return cursor.fetchall()

        except Error as e:
            print("Error retrieving project statistics:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 8. GET PROJECT ALLOCATION STATISTICS
    # --------------------------------------------------
    def get_project_allocation_statistics(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    p.project_name,

                    COUNT(f.allocation_sk)
                    AS total_assignments,

                    COUNT(DISTINCT f.employee_sk)
                    AS total_employees,

                    ROUND(AVG(f.allocation_percentage), 2)
                    AS average_allocation,

                    SUM(f.allocation_percentage)
                    AS total_allocation

                FROM Fact_ProjectAllocations f

                JOIN Dim_Project p
                    ON f.project_sk = p.project_sk

                GROUP BY p.project_sk, p.project_name

                ORDER BY total_assignments DESC
            """

            cursor.execute(query)

            return cursor.fetchall()

        except Error as e:
            print("Error retrieving project allocation statistics:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()
