"""MySQL-backed local accounts and role-based permissions."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from mysql.connector import Error

from src.database.db_manager import DatabaseConnection
from src.database.exceptions import DataAccessError

ROLES = ("Admin", "HR", "Executive")
ROLE_PERMISSIONS = {
    "Admin": frozenset({
        "manage_users", "manage_employees", "manage_projects",
        "submit_reviews", "sync_warehouse",
    }),
    "HR": frozenset({
        "manage_employees", "manage_projects", "submit_reviews",
        "sync_warehouse",
    }),
    "Executive": frozenset(),
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL,
    employee_id INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
    locked_until DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL,
    UNIQUE KEY uq_app_users_username (username),
    UNIQUE KEY uq_app_users_email (email),
    UNIQUE KEY uq_app_users_employee (employee_id),
    CONSTRAINT chk_app_users_role
        CHECK (role IN ('Admin', 'HR', 'Executive')),
    CONSTRAINT fk_app_users_employee
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
        ON DELETE SET NULL
) ENGINE=InnoDB
"""

_HASH_N = 1 << 14
_HASH_R = 8
_HASH_P = 1
_HASH_LENGTH = 32
_LOCKOUT_LIMIT = 5
_LOCKOUT_MINUTES = 15


class AuthenticationError(Exception):
    """A safe-to-display account or sign-in error."""


def create_auth_schema() -> None:
    """Create or safely migrate the account table to the current role set."""
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(_SCHEMA)
        cursor.execute(
            """
            SELECT check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = DATABASE()
              AND constraint_name = 'chk_app_users_role'
            """
        )
        constraint = cursor.fetchone()
        check_clause = (constraint[0] or "").upper() if constraint else ""
        if (
            "EXECUTIVE" not in check_clause
            or "MANAGER" in check_clause
            or "VIEWER" in check_clause
        ):
            if constraint:
                cursor.execute(
                    "ALTER TABLE app_users DROP CHECK chk_app_users_role"
                )
            cursor.execute(
                "UPDATE app_users SET role = 'Executive', employee_id = NULL "
                "WHERE role IN ('Manager', 'Viewer')"
            )
            cursor.execute(
                "ALTER TABLE app_users ADD CONSTRAINT chk_app_users_role "
                "CHECK (role IN ('Admin', 'HR', 'Executive'))"
            )
        connection.commit()
    except Error as err:
        connection.rollback()
        raise AuthenticationError(
            "Could not initialize IAM. Check that the OLTP database exists "
            "and the configured user can create tables."
        ) from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def _password_hash(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise AuthenticationError("Passwords must be at least 12 characters.")
    if len(password) > 1024:
        raise AuthenticationError("Password is too long.")

    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_HASH_N, r=_HASH_R,
        p=_HASH_P, dklen=_HASH_LENGTH,
    )
    return "scrypt${}${}${}${}${}".format(
        _HASH_N, _HASH_R, _HASH_P,
        salt.hex(), digest.hex(),
    )


def _verify_password(password: str, stored_hash: str) -> bool:
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    try:
        algorithm, n, r, p, salt_hex, digest_hex = stored_hash.split("$")
        if (
            algorithm != "scrypt"
            or int(n) != _HASH_N
            or int(r) != _HASH_R
            or int(p) != _HASH_P
            or len(bytes.fromhex(salt_hex)) != 16
            or len(bytes.fromhex(digest_hex)) != _HASH_LENGTH
        ):
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p),
            dklen=len(bytes.fromhex(digest_hex)),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError, OverflowError):
        return False


def _connection():
    db = DatabaseConnection()
    try:
        return db.get_connection(db.database_for("oltp"))
    except (DataAccessError, ValueError) as err:
        raise AuthenticationError(
            "Could not connect to the configured OLTP database."
        ) from err


def _validate_account(username: str, email: str, role: str) -> tuple[str, str]:
    username = (username or "").strip().lower()
    email = (email or "").strip().lower()
    if not 3 <= len(username) <= 64 or not all(
        char.isalnum() or char in "._-" for char in username
    ):
        raise AuthenticationError(
            "Username must be 3-64 characters and use letters, numbers, "
            "dots, underscores, or hyphens."
        )
    if len(email) > 254 or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise AuthenticationError("Enter a valid email address.")
    if role not in ROLES:
        raise AuthenticationError("Select a valid role.")
    return username, email


def create_user(username: str, email: str, password: str, role: str) -> int:
    username, email = _validate_account(username, email, role)
    encoded = _password_hash(password)
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO app_users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            """,
            (username, email, encoded, role),
        )
        connection.commit()
        return cursor.lastrowid
    except Error as err:
        connection.rollback()
        if err.errno == 1062:
            raise AuthenticationError(
                "That username, email, or employee already has an account."
            ) from err
        if err.errno == 1452:
            raise AuthenticationError("The linked employee does not exist.") from err
        raise AuthenticationError("Could not create the account.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def authenticate(username: str, password: str) -> dict | None:
    username = (username or "").strip().lower()
    if (
        not 3 <= len(username) <= 64
        or not isinstance(password, str)
        or len(password) > 1024
    ):
        return None

    connection = _connection()
    cursor = None
    try:
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, email, password_hash, role, "
            "is_active, failed_attempts, locked_until FROM app_users "
            "WHERE username = %s FOR UPDATE",
            (username,),
        )
        row = cursor.fetchone()
        if not row or not row["is_active"]:
            connection.rollback()
            return None

        now = datetime.now()
        locked_until = row["locked_until"]
        if locked_until and locked_until > now:
            connection.rollback()
            return None

        valid = _verify_password(password, row["password_hash"])
        if not valid:
            failures = int(row["failed_attempts"]) + 1
            lock_until = (
                now + timedelta(minutes=_LOCKOUT_MINUTES)
                if failures >= _LOCKOUT_LIMIT else None
            )
            cursor.execute(
                "UPDATE app_users SET failed_attempts = %s, locked_until = %s "
                "WHERE user_id = %s",
                (min(failures, 255), lock_until, row["user_id"]),
            )
            connection.commit()
            return None

        cursor.execute(
            "UPDATE app_users SET failed_attempts = 0, locked_until = NULL, "
            "last_login_at = %s WHERE user_id = %s",
            (now, row["user_id"]),
        )
        connection.commit()
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "email": row["email"],
            "role": row["role"],
        }
    except Error as err:
        connection.rollback()
        if err.errno == 1146:
            raise AuthenticationError(
                "IAM is not initialized. Run `uv run python -m "
                "src.auth.bootstrap_admin` to create the first administrator."
            ) from err
        raise AuthenticationError("Could not verify the account.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_active_user(user_id: int) -> dict | None:
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, email, role "
            "FROM app_users WHERE user_id = %s AND is_active = TRUE",
            (user_id,),
        )
        return cursor.fetchone()
    except Error as err:
        if err.errno == 1146:
            raise AuthenticationError(
                "IAM is not initialized. Run `uv run python -m "
                "src.auth.bootstrap_admin` to create the first administrator."
            ) from err
        raise AuthenticationError("Could not verify the account.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def list_users() -> list[dict]:
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT user_id, username, email, role, is_active, created_at,
                   last_login_at
            FROM app_users
            ORDER BY username
            """
        )
        return cursor.fetchall()
    except Error as err:
        raise AuthenticationError("Could not load IAM accounts.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def set_user_active(user_id: int, is_active: bool, acting_user_id: int) -> None:
    if user_id == acting_user_id and not is_active:
        raise AuthenticationError("You cannot deactivate your own account.")
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()
        cursor.execute(
            "SELECT role, is_active FROM app_users WHERE user_id = %s FOR UPDATE",
            (user_id,),
        )
        target = cursor.fetchone()
        if target is None:
            raise AuthenticationError("Account not found.")
        if target["role"] == "Admin" and target["is_active"] and not is_active:
            cursor.execute(
                "SELECT COUNT(*) AS n FROM app_users "
                "WHERE role = 'Admin' AND is_active = TRUE"
            )
            if cursor.fetchone()["n"] <= 1:
                raise AuthenticationError("At least one active administrator is required.")
        cursor.execute(
            "UPDATE app_users SET is_active = %s, failed_attempts = 0, "
            "locked_until = NULL WHERE user_id = %s",
            (bool(is_active), user_id),
        )
        connection.commit()
    except AuthenticationError:
        connection.rollback()
        raise
    except Error as err:
        connection.rollback()
        raise AuthenticationError("Could not update the account.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def reset_user_password(user_id: int, password: str) -> None:
    encoded = _password_hash(password)
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE app_users SET password_hash = %s, failed_attempts = 0, "
            "locked_until = NULL WHERE user_id = %s",
            (encoded, user_id),
        )
        if cursor.rowcount == 0:
            raise AuthenticationError("Account not found.")
        connection.commit()
    except AuthenticationError:
        connection.rollback()
        raise
    except Error as err:
        connection.rollback()
        raise AuthenticationError("Could not reset the password.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def update_user_role(user_id: int, role: str) -> None:
    if role not in ROLES:
        raise AuthenticationError("Select a valid role.")
    connection = _connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()
        cursor.execute(
            "SELECT role, is_active FROM app_users WHERE user_id = %s FOR UPDATE",
            (user_id,),
        )
        current = cursor.fetchone()
        if current is None:
            raise AuthenticationError("Account not found.")
        if current["role"] == "Admin" and current["is_active"] and role != "Admin":
            cursor.execute(
                "SELECT COUNT(*) AS n FROM app_users "
                "WHERE role = 'Admin' AND is_active = TRUE"
            )
            if cursor.fetchone()["n"] <= 1:
                raise AuthenticationError("At least one active administrator is required.")
        cursor.execute(
            "UPDATE app_users SET role = %s WHERE user_id = %s",
            (role, user_id),
        )
        connection.commit()
    except AuthenticationError:
        connection.rollback()
        raise
    except Error as err:
        connection.rollback()
        raise AuthenticationError("Could not update the account role.") from err
    finally:
        if cursor:
            cursor.close()
        connection.close()


def bootstrap_admin(username: str, email: str, password: str) -> int:
    create_auth_schema()
    connection = _connection()
    cursor = None
    lock_acquired = False
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT GET_LOCK('employee_analytics_first_admin', 10)"
        )
        lock_acquired = cursor.fetchone()[0] == 1
        if not lock_acquired:
            raise AuthenticationError("Could not lock IAM setup; try again.")
        cursor.execute("SELECT COUNT(*) FROM app_users WHERE role = 'Admin'")
        if cursor.fetchone()[0]:
            raise AuthenticationError(
                "An administrator already exists. Ask an administrator to "
                "create additional accounts."
            )
        return create_user(username, email, password, "Admin")
    except Error as err:
        raise AuthenticationError("Could not check existing IAM accounts.") from err
    finally:
        try:
            if cursor and lock_acquired:
                cursor.execute(
                    "SELECT RELEASE_LOCK('employee_analytics_first_admin')"
                )
                cursor.fetchone()
        finally:
            if cursor:
                cursor.close()
            connection.close()
