
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

        if self.employee_id is None:
            raise ValueError("Employee ID is required")

        if not self.review_date:
            raise ValueError("Review date is required")

        if not self.review_period:
            raise ValueError("Review period is required")

        if (
            self.performance_score is not None
            and not 1 <= self.performance_score <= 5
        ):
            raise ValueError("Performance score must be between 1 and 5")

        if (
            self.performance_rating is not None
            and not 1 <= self.performance_rating <= 5
        ):
            raise ValueError("Performance rating must be between 1 and 5")

        if (
            self.goal_achievement_pct is not None
            and not 0 <= self.goal_achievement_pct <= 130
        ):
            raise ValueError(
                "Goal achievement percentage must be between 0 and 130"
            )

        if (
            self.peer_feedback_score is not None
            and not 1 <= self.peer_feedback_score <= 5
        ):
            raise ValueError("Peer feedback score must be between 1 and 5")

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
