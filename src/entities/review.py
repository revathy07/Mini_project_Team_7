
class Review:

    # Constructor: initializes performance review details
    def __init__(
        self,
        employee_id,
        reviewer_id,
        review_date,
        review_period,
        performance_rating,
        job_satisfaction,
        work_life_balance,
        percent_salary_hike,
        comments=None,
        review_id=None
    ):

        # Review identification
        self.review_id = review_id
        self.employee_id = employee_id
        self.reviewer_id = reviewer_id

        # Review period
        self.review_date = review_date
        self.review_period = review_period

        # Performance details
        self.performance_rating = performance_rating
        self.job_satisfaction = job_satisfaction
        self.work_life_balance = work_life_balance
        self.percent_salary_hike = percent_salary_hike

        # Additional comments
        self.comments = comments

    # Checks whether the performance rating is good
    def is_good_performance(self):
        return self.performance_rating >= 4

    # Validates review information
    def validate(self):

        if self.employee_id is None:
            raise ValueError("Employee ID is required")

        if self.reviewer_id is None:
            raise ValueError("Reviewer ID is required")

        if not self.review_date:
            raise ValueError("Review date is required")

        if not self.review_period:
            raise ValueError("Review period is required")

        if not 1 <= self.performance_rating <= 5:
            raise ValueError("Performance rating must be between 1 and 5")

        if not 1 <= self.job_satisfaction <= 4:
            raise ValueError("Job satisfaction must be between 1 and 4")

        if not 1 <= self.work_life_balance <= 4:
            raise ValueError("Work-life balance must be between 1 and 4")

        if self.percent_salary_hike < 0:
            raise ValueError("Salary hike cannot be negative")

        return True

    # Displays review details
    def display_details(self):

        print("Review ID:", self.review_id)
        print("Employee ID:", self.employee_id)
        print("Reviewer ID:", self.reviewer_id)
        print("Review Date:", self.review_date)
        print("Review Period:", self.review_period)
        print("Performance Rating:", self.performance_rating)
        print("Job Satisfaction:", self.job_satisfaction)
        print("Work-Life Balance:", self.work_life_balance)
        print("Salary Hike:", self.percent_salary_hike)
        print("Comments:", self.comments)
