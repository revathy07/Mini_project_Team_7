import math
from datetime import date, datetime
from decimal import Decimal


def validate_text(value, label, max_length, optional=False):
    if optional and (
        value is None or (isinstance(value, str) and not value.strip())
    ):
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    if len(value) > max_length:
        raise ValueError(f"{label} cannot exceed {max_length} characters")


def validate_integer(value, label, minimum=None, maximum=None, optional=False):
    if value is None and optional:
        return
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be at most {maximum}")


def validate_number(
    value, label, minimum=None, maximum=None, optional=False, decimal_places=None
):
    if value is None and optional:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{label} must be numeric")
    if isinstance(value, Decimal):
        finite = value.is_finite()
    else:
        finite = math.isfinite(value)
    if not finite:
        raise ValueError(f"{label} must be finite")
    if decimal_places is not None:
        numeric_value = value if isinstance(value, Decimal) else Decimal(str(value))
        if max(0, -numeric_value.normalize().as_tuple().exponent) > decimal_places:
            raise ValueError(
                f"{label} cannot have more than {decimal_places} decimal places"
            )
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be at most {maximum}")


def validate_boolean(value, label, optional=False):
    if value is None and optional:
        return
    if not isinstance(value, bool) and not (
        type(value) is int and value in (0, 1)
    ):
        raise ValueError(f"{label} must be a boolean")


def parse_date(value, label, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            parsed = None
        if parsed is not None and parsed.isoformat() == value:
            return parsed
    raise ValueError(f"{label} must be a valid YYYY-MM-DD date")
