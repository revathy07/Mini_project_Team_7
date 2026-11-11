
from datetime import date

from src.entities.validation import (
    parse_date,
    validate_boolean,
    validate_integer,
    validate_number,
    validate_text,
)


class Review:

    # Constructor: initializes performance review details
    def __init__(
        self,
        employee_id,
        review_date,
        review_period,
        reviewer_id=None,
        performance_score=None,
        performance_rating=None,
        goal_achievement_pct=None,
        peer_feedback_score=None,
        promotion_recommended=False,
        comments=None,
        review_id=None
    ):

        # Review identification
        self.review_id = review_id
        self.employee_id = employee_id
        self.reviewer_id = reviewer_id

        # Review dates
        self.review_date = review_date
        self.review_period = review_period

        # Performance measurements
        self.performance_score = performance_score
        self.performance_rating = performance_rating
        self.goal_achievement_pct = goal_achievement_pct
        self.peer_feedback_score = peer_feedback_score

        # Additional review information
        self.promotion_recommended = promotion_recommended
        self.comments = comments

    # Checks whether the employee has good performance
    def is_good_performance(self):
        return (
            self.performance_rating is not None
            and self.performance_rating >= 4
        )

    # Validates review information
    def validate(self):

        validate_integer(self.employee_id, "Employee ID", minimum=1)
        validate_integer(
            self.reviewer_id, "Reviewer ID", minimum=1, optional=True
        )
        if self.reviewer_id == self.employee_id:
            raise ValueError("An employee cannot review themselves")
        validate_integer(self.review_id, "Review ID", minimum=1, optional=True)
        review_date = parse_date(self.review_date, "Review date")
        if review_date > date.today():
            raise ValueError("Review date cannot be in the future")
        if review_date.year < 2010:
            raise ValueError("Review date must be 2010 or later")
        validate_text(self.review_period, "Review period", 20)
        validate_number(
            self.performance_score, "Performance score",
            minimum=1, maximum=5, optional=True, decimal_places=2,
        )
        validate_integer(
            self.performance_rating, "Performance rating",
            minimum=1, maximum=5, optional=True,
        )
        validate_number(
            self.goal_achievement_pct, "Goal achievement percentage",
            minimum=0, maximum=130, optional=True, decimal_places=1,
        )
        validate_number(
            self.peer_feedback_score, "Peer feedback score",
            minimum=1, maximum=5, optional=True, decimal_places=2,
        )
        validate_boolean(self.promotion_recommended, "Promotion recommendation")
        validate_text(self.comments, "Review comments", 65535, optional=True)
        if (
            self.comments is not None
            and len(self.comments.encode("utf-8")) > 65535
        ):
            raise ValueError("Review comments exceed the database text limit")

        return True

    # Displays review details
    def display_details(self):

        print("\n----- Performance Review Details -----")
        print("Review ID:", self.review_id)
        print("Employee ID:", self.employee_id)
        print("Reviewer ID:", self.reviewer_id)
        print("Review Date:", self.review_date)
        print("Review Period:", self.review_period)
        print("Performance Score:", self.performance_score)
        print("Performance Rating:", self.performance_rating)
        print("Goal Achievement:", self.goal_achievement_pct)
        print("Peer Feedback:", self.peer_feedback_score)
        print("Promotion Recommended:", self.promotion_recommended)
        print("Comments:", self.comments)
