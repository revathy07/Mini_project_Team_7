
from mysql.connector import Error
from src.database.base_manager import BaseManager


class AnalyticsManager(BaseManager):

    database_kind = "dw"

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
                WHERE is_current = 1 AND attrition_flag = 0
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
                WHERE is_current = 1 AND attrition_flag = 0
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

        # --------------------------------------------------
    # 9. REVIEW YEAR RANGE (for the year slider)
    # --------------------------------------------------
    def get_review_year_range(self):
        return self.fetch_one(
            "SELECT MIN(date_key) DIV 10000 AS min_year, "
            "       MAX(date_key) DIV 10000 AS max_year "
            "FROM Fact_PerformanceReviews"
        )

    # --------------------------------------------------
    # 10. YEARLY TREND PER DEPARTMENT
    #     department_sk = department the employee had ON the review date (SCD2)
    # --------------------------------------------------
    def get_yearly_trend_by_department(self):
        return self.fetch_all("""
            SELECT dt.year,
                   dd.department_name,
                   ROUND(AVG(f.performance_score), 2) AS avg_score,
                   COUNT(*) AS reviews
            FROM Fact_PerformanceReviews f
            JOIN Dim_Date dt       ON dt.date_key = f.date_key
            JOIN Dim_Department dd ON dd.department_sk = f.department_sk
            GROUP BY dt.year, dd.department_name
            ORDER BY dt.year, dd.department_name
        """)

    # --------------------------------------------------
    # 11. TOP PERFORMERS PER DEPARTMENT (CTE + DENSE_RANK)
    #     Active employees only. Department = current department.
    # --------------------------------------------------
    def get_top_performers(self, year_from, year_to, min_reviews=3, top_n=5):
        return self.fetch_all("""
            WITH emp_scores AS (
                SELECT cur.employee_code,
                       cur.full_name,
                       cur.department_name,
                       cur.job_role,
                       ROUND(AVG(f.performance_score), 2)    AS avg_score,
                       ROUND(AVG(f.goal_achievement_pct), 1) AS avg_goal,
                       COUNT(*)                              AS review_count
                FROM Fact_PerformanceReviews f
                JOIN Dim_Employee de  ON de.employee_sk = f.employee_sk
                JOIN Dim_Employee cur ON cur.employee_code = de.employee_code
                                     AND cur.is_current = 1
                WHERE f.date_key BETWEEN %s AND %s
                  AND cur.attrition_flag = 0
                GROUP BY cur.employee_code, cur.full_name,
                         cur.department_name, cur.job_role
                HAVING COUNT(*) >= %s
            ),
            ranked AS (
                SELECT emp_scores.*,
                       DENSE_RANK() OVER (
                           PARTITION BY department_name
                           ORDER BY avg_score DESC, review_count DESC
                       ) AS dept_rank
                FROM emp_scores
            )
            SELECT department_name, dept_rank, employee_code, full_name,
                   job_role, avg_score, avg_goal, review_count
            FROM ranked
            WHERE dept_rank <= %s
            ORDER BY department_name, dept_rank, employee_code
        """, (int(year_from) * 10000 + 101, int(year_to) * 10000 + 1231,
              int(min_reviews), int(top_n)))

    # --------------------------------------------------
    # 12. PROJECT DELAY (completed projects only)
    # --------------------------------------------------
    def get_project_delay_summary(self):
        return self.fetch_all("""
            SELECT department_name,
                   priority,
                   COUNT(*) AS projects,
                   ROUND(AVG(DATEDIFF(end_date, planned_end_date)), 1) AS avg_delay_days,
                   ROUND(100 * AVG(end_date > planned_end_date), 1)    AS pct_delayed
            FROM Dim_Project
            WHERE status = 'Completed'
              AND end_date IS NOT NULL
              AND planned_end_date IS NOT NULL
            GROUP BY department_name, priority
            ORDER BY department_name,
                     FIELD(priority, 'Low', 'Medium', 'High', 'Critical')
        """)

    # --------------------------------------------------
    # 13. OVERDUE OPEN PROJECTS (COUNT() OVER gives the full total before LIMIT)
    # --------------------------------------------------
    def get_overdue_projects(self, limit=25):
        return self.fetch_all("""
            SELECT project_code, project_name, department_name, priority, status,
                   planned_end_date,
                   DATEDIFF(CURDATE(), planned_end_date) AS days_overdue,
                   budget,
                   COUNT(*) OVER () AS total_overdue
            FROM Dim_Project
            WHERE status IN ('Active', 'On Hold')
              AND planned_end_date < CURDATE()
            ORDER BY days_overdue DESC, budget DESC
            LIMIT %s
        """, (int(limit),))
