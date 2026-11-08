
from mysql.connector import Error
from src.database.db_manager import DatabaseConnection
from src.entities.review import Review


class ReviewManager(DatabaseConnection):

    def __init__(self):
        super().__init__()
        self.database_name = "employee_oltp"

    # --------------------------------------------------
    # 1. ADD PERFORMANCE REVIEW
    # --------------------------------------------------
    def add_review(self, review):

        connection = None
        cursor = None

        try:
            # Validate review details
            review.validate()

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                INSERT INTO Performance_Reviews (
                    employee_id,
                    reviewer_id,
                    review_date,
                    review_period,
                    performance_score,
                    performance_rating,
                    goal_achievement_pct,
                    peer_feedback_score,
                    promotion_recommended,
                    comments
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                review.employee_id,
                review.reviewer_id,
                review.review_date,
                review.review_period,
                review.performance_score,
                review.performance_rating,
                review.goal_achievement_pct,
                review.peer_feedback_score,
                review.promotion_recommended,
                review.comments
            )

            cursor.execute(query, values)
            connection.commit()

            # Store the generated ID in the Review object
            review.review_id = cursor.lastrowid

            print("Performance review added successfully.")

            return review.review_id

        except ValueError as e:
            print("Review validation failed:", e)
            raise

        except Error as e:
            if connection:
                connection.rollback()

            print("Database error while adding review:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()

            print("Unexpected error while adding review:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 2. GET REVIEW BY ID
    # --------------------------------------------------
    def get_review_by_id(self, review_id):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Performance_Reviews
                WHERE review_id = %s
            """

            cursor.execute(query, (review_id,))

            result = cursor.fetchone()

            if result is None:
                print("Performance review not found.")
                return None

            return Review(**result)

        except Error as e:
            print("Database error while retrieving review:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 3. GET ALL REVIEWS
    # --------------------------------------------------
    def get_all_reviews(self):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Performance_Reviews
                ORDER BY review_date DESC
            """

            cursor.execute(query)

            results = cursor.fetchall()

            reviews = []

            for row in results:
                review = Review(**row)
                reviews.append(review)

            return reviews

        except Error as e:
            print("Database error while retrieving reviews:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 4. GET REVIEWS FOR A PARTICULAR EMPLOYEE
    # --------------------------------------------------
    def get_employee_reviews(self, employee_id):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM Performance_Reviews
                WHERE employee_id = %s
                ORDER BY review_date DESC
            """

            cursor.execute(query, (employee_id,))

            results = cursor.fetchall()

            reviews = []

            for row in results:
                review = Review(**row)
                reviews.append(review)

            return reviews

        except Error as e:
            print("Database error while retrieving employee reviews:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 5. UPDATE PERFORMANCE REVIEW
    # --------------------------------------------------
    def update_review(self, review_id, updated_fields):

        connection = None
        cursor = None

        allowed_fields = {
            "employee_id",
            "reviewer_id",
            "review_date",
            "review_period",
            "performance_score",
            "performance_rating",
            "goal_achievement_pct",
            "peer_feedback_score",
            "promotion_recommended",
            "comments"
        }

        try:
            if not updated_fields:
                raise ValueError("No review details provided for update")

            # Check whether all fields are allowed
            for field in updated_fields:

                if field not in allowed_fields:
                    raise ValueError(
                        "Updating this review field is not allowed: "
                        + field
                    )

            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            set_clause = ", ".join(
                [f"{field} = %s" for field in updated_fields]
            )

            query = f"""
                UPDATE Performance_Reviews
                SET {set_clause}
                WHERE review_id = %s
            """

            values = tuple(updated_fields.values()) + (review_id,)

            cursor.execute(query, values)

            if cursor.rowcount == 0:

                cursor.execute(
                    """
                    SELECT review_id
                    FROM Performance_Reviews
                    WHERE review_id = %s
                    """,
                    (review_id,)
                )

                if cursor.fetchone() is None:
                    raise ValueError("Performance review not found")

            connection.commit()

            print("Performance review updated successfully.")

            return True

        except (ValueError, Error) as e:
            if connection:
                connection.rollback()

            print("Error while updating review:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()

            print("Unexpected error while updating review:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    # --------------------------------------------------
    # 6. DELETE PERFORMANCE REVIEW
    # --------------------------------------------------
    def delete_review(self, review_id):

        connection = None
        cursor = None

        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor()

            query = """
                DELETE FROM Performance_Reviews
                WHERE review_id = %s
            """

            cursor.execute(query, (review_id,))

            if cursor.rowcount == 0:
                raise ValueError("Performance review not found")

            connection.commit()

            print("Performance review deleted successfully.")

            return True

        except (ValueError, Error) as e:
            if connection:
                connection.rollback()

            print("Error while deleting review:", e)
            raise

        except Exception as e:
            if connection:
                connection.rollback()

            print("Unexpected error while deleting review:", e)
            raise

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()
