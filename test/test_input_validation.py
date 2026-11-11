from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.entities.employee import Employee
from src.entities.project import Project
from src.entities.review import Review
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager
from src.managers.review_manager import ReviewManager


def employee(**overrides):
    fields = {
        "employee_code": "EMP-000001",
        "first_name": "Avery",
        "last_name": "Morgan",
        "email": "avery@example.com",
        "hire_date": date(2020, 1, 1),
        "job_role": "Analyst",
        "monthly_income": Decimal("50000.00"),
        "department_id": 1,
        "age": 30,
        "job_level": 2,
        "attrition": False,
        "status": "Active",
    }
    return Employee(**(fields | overrides))


def project(**overrides):
    fields = {
        "project_code": "PROJ-00001",
        "project_name": "Analytics",
        "start_date": date(2025, 1, 1),
        "planned_end_date": date(2025, 6, 1),
        "department_id": 1,
        "budget": Decimal("10000.00"),
        "status": "Active",
        "priority": "High",
    }
    return Project(**(fields | overrides))


def review(**overrides):
    fields = {
        "employee_id": 1,
        "reviewer_id": 2,
        "review_date": date.today(),
        "review_period": "2026-Annual",
        "performance_score": Decimal("4.25"),
        "performance_rating": 4,
        "goal_achievement_pct": Decimal("95.0"),
        "peer_feedback_score": Decimal("4.0"),
        "promotion_recommended": False,
    }
    return Review(**(fields | overrides))


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"first_name": " "}, "First name"),
        ({"email": "not-an-email"}, "valid email"),
        ({"email": "a" * 95 + "@b.com"}, "valid email"),
        ({"monthly_income": True}, "numeric"),
        ({"monthly_income": float("inf")}, "finite"),
        ({"monthly_income": 0}, "at least"),
        ({"monthly_income": Decimal("12.345")}, "decimal places"),
        ({"department_id": 1.5}, "integer"),
        ({"age": True}, "integer"),
        ({"age": 71}, "at most"),
        ({"job_level": 0}, "at least"),
        ({"percent_salary_hike": 101}, "at most"),
        ({"distance_from_home": -1}, "at least"),
        ({"job_satisfaction": 5}, "at most"),
        ({"total_working_years": -1}, "at least"),
        ({"total_working_years": 20, "age": 30}, "age minus 18"),
        ({"hire_date": "2024-02-30"}, "valid YYYY-MM-DD"),
        ({"termination_date": date(2019, 12, 31)}, "before hire date"),
        ({"attrition": "false"}, "boolean"),
    ],
)
def test_employee_rejects_invalid_values(fields, message):
    with pytest.raises(ValueError, match=message):
        employee(**fields).validate()


def test_employee_accepts_supported_date_inputs_and_optional_values():
    assert employee(
        hire_date="2020-01-01",
        termination_date=None,
        job_satisfaction=None,
        overtime=None,
        business_travel="",
        gender="",
    ).validate()
    assert employee(monthly_income=Decimal("50000.000")).validate()


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"project_name": " "}, "Project name"),
        ({"project_name": "x" * 151}, "150 characters"),
        ({"start_date": "tomorrow"}, "valid YYYY-MM-DD"),
        ({"planned_end_date": date(2024, 12, 31)}, "before start date"),
        ({"budget": float("nan")}, "finite"),
        ({"budget": -1}, "at least"),
        ({"budget": Decimal("12.345")}, "decimal places"),
        ({"project_manager_id": 1.2}, "integer"),
        ({"status": "Unknown"}, "Project status"),
        ({"priority": "Urgent"}, "Project priority"),
    ],
)
def test_project_rejects_invalid_values(fields, message):
    with pytest.raises(ValueError, match=message):
        project(**fields).validate()


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"employee_id": 0}, "at least"),
        ({"reviewer_id": 1}, "cannot review themselves"),
        ({"review_date": "2026-15-01"}, "valid YYYY-MM-DD"),
        ({"review_date": date.today() + timedelta(days=1)}, "future"),
        ({"review_date": date(2009, 12, 31)}, "2010 or later"),
        ({"review_period": " "}, "Review period"),
        ({"performance_score": 5.1}, "at most"),
        ({"performance_score": Decimal("4.125")}, "decimal places"),
        ({"performance_rating": 2.5}, "integer"),
        ({"goal_achievement_pct": -0.1}, "at least"),
        ({"goal_achievement_pct": Decimal("80.25")}, "decimal places"),
        ({"peer_feedback_score": float("inf")}, "finite"),
        ({"promotion_recommended": "yes"}, "boolean"),
    ],
)
def test_review_rejects_invalid_values(fields, message):
    with pytest.raises(ValueError, match=message):
        review(**fields).validate()


def manager_with_existing_row(manager_class, row):
    manager = manager_class.__new__(manager_class)
    manager.database_name = "employee_oltp"
    connection = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = row
    connection.cursor.return_value = cursor
    connection.is_connected.return_value = True
    manager.get_connection = Mock(return_value=connection)
    return manager, connection, cursor


def test_employee_update_validates_merged_record_before_writing():
    row = employee().__dict__
    manager, connection, cursor = manager_with_existing_row(EmployeeManager, row)

    with pytest.raises(ValueError, match="Age"):
        manager.update_employee(1, {"age": 17})

    assert cursor.execute.call_count == 1
    connection.rollback.assert_called_once()


def test_employee_rejects_self_as_manager():
    with pytest.raises(ValueError, match="cannot be their own manager"):
        employee(employee_id=1, manager_id=1).validate()


def test_project_update_validates_date_relationship_before_writing():
    row = project().__dict__
    manager, connection, cursor = manager_with_existing_row(ProjectManager, row)

    with pytest.raises(ValueError, match="before start date"):
        manager.update_project(1, {"planned_end_date": date(2024, 12, 31)})

    assert cursor.execute.call_count == 1
    connection.rollback.assert_called_once()


def test_review_update_validates_self_review_before_writing():
    row = review().__dict__
    manager, connection, cursor = manager_with_existing_row(ReviewManager, row)

    with pytest.raises(ValueError, match="cannot review themselves"):
        manager.update_review(1, {"reviewer_id": 1})

    assert cursor.execute.call_count == 1
    connection.rollback.assert_called_once()


def test_assignment_rejects_allocation_over_one_hundred_before_database_access():
    manager = ProjectManager.__new__(ProjectManager)
    manager.get_connection = Mock()

    with pytest.raises(ValueError, match="at most 100"):
        manager.assign_employee(
            employee_id=1,
            project_id=1,
            start_date=date.today(),
            allocation_percentage=101,
        )

    manager.get_connection.assert_not_called()


def test_assignment_rejects_invalid_date_before_database_access():
    manager = ProjectManager.__new__(ProjectManager)
    manager.get_connection = Mock()

    with pytest.raises(ValueError, match="valid YYYY-MM-DD"):
        manager.assign_employee(
            employee_id=1,
            project_id=1,
            start_date="not-a-date",
        )

    manager.get_connection.assert_not_called()


@pytest.mark.parametrize(
    "employee_record",
    [
        (date(2025, 1, 1), None),
        {"hire_date": date(2025, 1, 1), "termination_date": None},
    ],
)
def test_review_date_must_fall_within_employee_tenure(employee_record):
    cursor = Mock()
    cursor.fetchone.return_value = employee_record

    with pytest.raises(ValueError, match="before the hire date"):
        ReviewManager._validate_employee_tenure(
            cursor, review(review_date=date(2024, 12, 31))
        )

    cursor.execute.assert_called_once()
