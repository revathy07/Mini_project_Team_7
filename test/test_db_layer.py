"""Unit tests for the data layer. They use a fake connection pool, so they
need NO MySQL server and never touch real data.

Run:  uv run pytest test/test_db_layer.py -v
"""
import pytest
from mysql.connector import errors as mysql_errors

from src.database import db_manager
from src.database.base_manager import BaseManager
from src.database.db_manager import DatabaseConnection
from src.database.exceptions import (
    ConnectionFailedError, DataAccessError, DuplicateRecordError,
    IntegrityViolationError, NotFoundError, ValidationError,
    translate_mysql_error,
)


# ---------- fakes ----------
class FakeCursor:
    rowcount, lastrowid = 1, 42

    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        self.conn.log.append(("execute", sql))
        if self.conn.fail_with:
            raise self.conn.fail_with

    def fetchall(self):
        return self.conn.rows

    def fetchone(self):
        return self.conn.rows[0] if self.conn.rows else None

    def close(self):
        pass


class FakeConn:
    def __init__(self):
        self.log, self.rows, self.fail_with, self.closed = [], [], None, 0

    def cursor(self, dictionary=False):
        return FakeCursor(self)

    def commit(self):
        self.log.append("commit")

    def rollback(self):
        self.log.append("rollback")

    def close(self):
        self.closed += 1


class FakePool:
    created, fail_with = [], None

    def __init__(self, **kwargs):
        if FakePool.fail_with:
            raise FakePool.fail_with
        self.kwargs, self.conn = kwargs, FakeConn()
        FakePool.created.append(self)

    def get_connection(self):
        return self.conn


class OltpManager(BaseManager):
    database_kind = "oltp"


class DwManager(BaseManager):
    database_kind = "dw"


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "tester")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    for name in ("DB_OLTP", "DB_DW", "DB_STAGING", "DB_SSL_CA", "DB_POOL_SIZE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(db_manager.pooling, "MySQLConnectionPool", FakePool)
    FakePool.created, FakePool.fail_with = [], None
    DatabaseConnection._reset_for_tests()
    yield
    DatabaseConnection._reset_for_tests()


# ---------- singleton ----------
def test_same_class_returns_same_instance():
    assert OltpManager() is OltpManager()


def test_base_created_first_does_not_break_subclasses():
    """Regression: the old __new__ handed a plain DatabaseConnection to subclasses."""
    base = DatabaseConnection()
    manager = OltpManager()
    assert type(manager) is OltpManager
    assert manager is not base
    assert hasattr(manager, "fetch_all")


def test_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD")
    with pytest.raises(ValueError, match="DB_PASSWORD"):
        OltpManager()


# ---------- config and pooling ----------
def test_database_names_default_and_override(monkeypatch):
    assert DatabaseConnection.database_for("oltp") == "employee_oltp"
    monkeypatch.setenv("DB_DW", "cloud_dw")
    assert DatabaseConnection.database_for("dw") == "cloud_dw"
    with pytest.raises(ValueError):
        DatabaseConnection.database_for("nope")


def test_one_pool_per_database_shared_between_managers():
    OltpManager().fetch_all("SELECT 1")
    OltpManager().fetch_all("SELECT 1")
    class SecondOltp(BaseManager):
        database_kind = "oltp"
    SecondOltp().fetch_all("SELECT 1")
    assert len(FakePool.created) == 1                  # shared
    DwManager().fetch_all("SELECT 1")
    assert len(FakePool.created) == 2                  # one per database


def test_ssl_ca_is_passed_to_the_pool(monkeypatch):
    monkeypatch.setenv("DB_SSL_CA", "/certs/ca.pem")
    OltpManager().fetch_all("SELECT 1")
    assert FakePool.created[0].kwargs["ssl_ca"] == "/certs/ca.pem"


# ---------- transactions ----------
def test_commit_and_connection_returned_on_success():
    manager = OltpManager()
    rows = manager.fetch_all("SELECT 1")
    conn = FakePool.created[0].conn
    assert "commit" in conn.log and "rollback" not in conn.log
    assert conn.closed == 1 and rows == []


def test_execute_returns_rowcount_and_last_id():
    assert OltpManager().execute("UPDATE x SET y = 1") == (1, 42)


def test_rollback_on_error_and_connection_still_returned():
    manager = OltpManager()
    manager.fetch_all("SELECT 1")                      # create the pool
    conn = FakePool.created[0].conn
    conn.log.clear()
    conn.fail_with = mysql_errors.DatabaseError("boom", errno=9999)
    with pytest.raises(DataAccessError):
        manager.execute("UPDATE x SET y = 1")
    assert "rollback" in conn.log and "commit" not in conn.log
    assert conn.closed == 2


def test_multi_statement_transaction_is_atomic():
    manager = OltpManager()
    manager.fetch_all("SELECT 1")
    conn = FakePool.created[0].conn
    conn.log.clear()
    with pytest.raises(RuntimeError):
        with manager.transaction() as cur:
            cur.execute("UPDATE a")
            raise RuntimeError("second step failed")
    assert conn.log[-1] == "rollback" and "commit" not in conn.log


def test_value_errors_pass_through_with_rollback():
    manager = OltpManager()
    manager.fetch_all("SELECT 1")
    conn = FakePool.created[0].conn
    with pytest.raises(ValueError):
        with manager.transaction():
            raise ValueError("bad input")
    assert "rollback" in conn.log


# ---------- error translation ----------
def test_duplicate_email_is_friendly():
    err = mysql_errors.IntegrityError(
        "Duplicate entry 'a@b.com' for key 'employees.email'", errno=1062)
    out = translate_mysql_error(err)
    assert isinstance(out, DuplicateRecordError)
    assert "email" in str(out).lower()


def test_duplicate_review_key_is_friendly():
    err = mysql_errors.IntegrityError(
        "Duplicate entry '5-2026-01-01' for key 'performance_reviews.uk_review'",
        errno=1062)
    assert "review" in str(translate_mysql_error(err)).lower()


def test_old_style_key_name_without_table_prefix():
    err = mysql_errors.IntegrityError("Duplicate entry 'x' for key 'email'", errno=1062)
    assert isinstance(translate_mysql_error(err), DuplicateRecordError)


def test_foreign_key_errors():
    child = mysql_errors.IntegrityError("Cannot add or update a child row", errno=1452)
    parent = mysql_errors.IntegrityError("Cannot delete or update a parent row", errno=1451)
    assert isinstance(translate_mysql_error(child), IntegrityViolationError)
    assert "still used" in str(translate_mysql_error(parent))


def test_check_constraint_becomes_validation_error():
    err = mysql_errors.DatabaseError("Check constraint violated", errno=3819)
    out = translate_mysql_error(err)
    assert isinstance(out, ValidationError) and isinstance(out, ValueError)


def test_not_found_is_also_a_value_error():
    assert issubclass(NotFoundError, ValueError)


def test_unreachable_database_raises_connection_failed():
    FakePool.fail_with = mysql_errors.InterfaceError(
        "Can't connect to MySQL server", errno=2003)
    with pytest.raises(ConnectionFailedError):
        OltpManager().fetch_all("SELECT 1")


def test_ping_reports_health():
    assert OltpManager().ping("employee_oltp") is True
    DatabaseConnection._reset_for_tests()
    FakePool.fail_with = mysql_errors.InterfaceError("down", errno=2003)
    assert OltpManager().ping("employee_oltp") is False