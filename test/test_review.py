from src.entities.review import Review

review = Review(
    employee_id=101,
    review_date="2026-06-15",
    review_period="2026-Q2",
    reviewer_id=102,
    performance_score=4.5,
    performance_rating=4,
    goal_achievement_pct=95.5,
    peer_feedback_score=4.2,
    promotion_recommended=True,
    comments="Excellent performance"
)

print("Good Performance:", review.is_good_performance())
print("Validation:", review.validate())

review.display_details()