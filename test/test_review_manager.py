
from src.managers.review_manager import ReviewManager
from src.entities.review import Review


# Create ReviewManager object
manager = ReviewManager()

# Create a sample performance review
review = Review(
    employee_id=1,
    reviewer_id=2,
    review_date="2026-11-08",
    review_period="Q4 2026",
    performance_score=4.5,
    performance_rating=5,
    goal_achievement_pct=95.0,
    peer_feedback_score=4.2,
    promotion_recommended=True,
    comments="Excellent performance and teamwork."
)

# 1. Add review
review_id = manager.add_review(review)
print("Generated Review ID:", review_id)

# 2. Retrieve review by ID
retrieved_review = manager.get_review_by_id(review_id)

if retrieved_review:
    retrieved_review.display_details()

# 3. Retrieve all reviews for an employee
employee_reviews = manager.get_employee_reviews(1)

print("\nEmployee Reviews:")

for item in employee_reviews:
    item.display_details()

# 4. Update review
manager.update_review(
    review_id,
    {
        "performance_rating": 4,
        "comments": "Very good performance."
    }
)

# 5. Retrieve all reviews
all_reviews = manager.get_all_reviews()

print("\nTotal reviews retrieved:", len(all_reviews))

# 6. Delete the test review
manager.delete_review(review_id)
