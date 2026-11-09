"""Exceptions raised by the data-access layer.

Managers translate raw MySQL errors into these classes, so UI code only needs:

    try:
        manager.add_employee(emp)
    except DataAccessError as err:
        st.error(str(err))          # message is safe to show to users

The original MySQL error stays available as ``err.__cause__`` for logs.
ValidationError and NotFoundError also inherit from ValueError, so existing
``except ValueError`` blocks keep working while code is migrated.
"""
import re

from mysql.connector import errors as mysql_errors


class DataAccessError(Exception):
    """Base class for every error the data layer raises."""

    def __init__(self, message, errno=None):
        super().__init__(message)
        self.errno = errno


class ConnectionFailedError(DataAccessError):
    """The database could not be reached (or the pool is exhausted)."""


class DuplicateRecordError(DataAccessError):
    """A UNIQUE constraint was violated (email, employee_code, ...)."""


class IntegrityViolationError(DataAccessError):
    """A foreign key was violated (missing parent, or row still referenced)."""


class ValidationError(DataAccessError, ValueError):
    """Input was rejected, by entity validation or by a column constraint."""


class NotFoundError(DataAccessError, ValueError):
    """The requested record does not exist."""


class WarehouseSyncError(DataAccessError):
    """OLTP was updated but the warehouse refresh failed (safe to retry)."""


_DUPLICATE_MESSAGES = {
    "email": "An employee with this email address already exists.",
    "employee_code": "An employee with this employee code already exists.",
    "project_code": "A project with this project code already exists.",
    "department_code": "A department with this code already exists.",
    "uk_review": "A review for this employee on this date already exists.",
    "uk_assign": "This employee is already assigned to this project "
                 "with the same start date.",
}
_DUPLICATE_KEY = re.compile(r"for key '([^']+)'")

# errno groups (MySQL server / client error codes)
_CONNECTION_ERRNOS = {1044, 1045, 1049, 1130, 2002, 2003, 2005, 2006, 2013, 2055}
_VALUE_ERRNOS = {1048, 1264, 1292, 1366, 1406, 3819}   # NULL, range, date, type, length, CHECK


def translate_mysql_error(err):
    """Turn a mysql.connector error into the matching DataAccessError."""
    if isinstance(err, DataAccessError):
        return err

    errno = getattr(err, "errno", None)
    raw = getattr(err, "msg", None) or str(err)

    if errno == 1062:
        match = _DUPLICATE_KEY.search(raw)
        key = match.group(1).split(".")[-1] if match else None
        message = _DUPLICATE_MESSAGES.get(
            key, f"A record with the same value already exists (key: {key})."
        )
        return DuplicateRecordError(message, errno)

    if errno == 1452:
        return IntegrityViolationError(
            "A referenced department, employee or project does not exist.", errno)
    if errno == 1451:
        return IntegrityViolationError(
            "This record is still used by other records and cannot be removed.", errno)

    if errno in _VALUE_ERRNOS:
        return ValidationError(f"A value is missing or out of range ({raw}).", errno)

    if (errno in _CONNECTION_ERRNOS
            or isinstance(err, (mysql_errors.PoolError, mysql_errors.InterfaceError))):
        return ConnectionFailedError(
            "Cannot reach the database right now. Please try again shortly.", errno)

    return DataAccessError(
        "A database error occurred. Please try again or contact support.", errno)