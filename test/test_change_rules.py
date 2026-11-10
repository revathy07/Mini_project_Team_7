from datetime import date
from decimal import Decimal

from src.managers.employee_manager import EmployeeManager, classify_change

BASE = {"department_id": 1, "job_role": "Sales Executive",
        "job_level": 2, "monthly_income": Decimal("5000.00")}


def changed(**overrides):
    return {**BASE, **overrides}


def test_department_change_wins_over_everything():
    new = changed(department_id=2, job_level=3, monthly_income=Decimal("9000.00"))
    assert classify_change(BASE, new) == "Department Transfer"


def test_level_up_is_promotion():
    assert classify_change(BASE, changed(job_level=3)) == "Promotion"


def test_level_down_is_demotion():
    assert classify_change(BASE, changed(job_level=1)) == "Demotion"


def test_pay_up_and_down():
    assert classify_change(BASE, changed(monthly_income=Decimal("5500.00"))) == "Salary Increase"
    assert classify_change(BASE, changed(monthly_income=Decimal("4500.00"))) == "Salary Adjustment"


def test_role_only_change():
    assert classify_change(BASE, changed(job_role="Sales Representative")) == "Role Change"


def test_no_change_returns_none():
    assert classify_change(BASE, dict(BASE)) is None


def test_floor_is_hire_date_without_events():
    assert EmployeeManager._floor_from(date(2020, 1, 10), None, None) == date(2020, 1, 10)


def test_floor_is_day_after_latest_event():
    floor = EmployeeManager._floor_from(date(2020, 1, 10), date(2025, 3, 1), date(2025, 6, 15))
    assert floor == date(2025, 6, 16)


def test_floor_ignores_events_before_hire():
    assert EmployeeManager._floor_from(date(2020, 1, 10), date(2019, 1, 1), None) == date(2020, 1, 10)