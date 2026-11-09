
from src.managers.analytics_manager import AnalyticsManager

# Create AnalyticsManager object
manager = AnalyticsManager()


# 1. Total employees
print("\n========== EMPLOYEE HEADCOUNT ==========")

total = manager.get_total_employees()
print("Total employees:", total)


# 2. Department distribution
print("\n========== DEPARTMENT DISTRIBUTION ==========")

departments = manager.get_department_distribution()

for department in departments:
    print(department)


# 3. Attrition statistics
print("\n========== ATTRITION STATISTICS ==========")

attrition = manager.get_attrition_statistics()
print(attrition)


# 4. Average performance
print("\n========== AVERAGE PERFORMANCE ==========")

performance = manager.get_average_performance()
print(performance)


# 5. Department performance
print("\n========== DEPARTMENT PERFORMANCE ==========")

department_performance = manager.get_department_performance()

for department in department_performance:
    print(department)


# 6. Yearly performance trend
print("\n========== YEARLY PERFORMANCE TREND ==========")

yearly_trend = manager.get_yearly_performance_trend()

for year in yearly_trend:
    print(year)


# 7. Project status distribution
print("\n========== PROJECT STATUS ==========")

project_status = manager.get_project_status_distribution()

for project in project_status:
    print(project)


# 8. Project allocation statistics
print("\n========== PROJECT ALLOCATIONS ==========")

allocations = manager.get_project_allocation_statistics()

for allocation in allocations:
    print(allocation)
