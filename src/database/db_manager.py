"""DatabaseConnection: Singleton that owns configuration and connection pools.

Design notes
------------
* One instance PER CLASS (so ``EmployeeManager()`` always returns the same
  EmployeeManager, and creating ``DatabaseConnection()`` first can never
  hand back the wrong type to a subclass).
* Pools are shared by every instance: one pool per database, created lazily.
  Callers keep using ``get_connection(name)`` / ``connection.close()``;
  ``close()`` on a pooled connection returns it to the pool.
* Database names come from .env (DB_OLTP, DB_DW, DB_STAGING) so a cloud
  provider's names can be used without code changes.
"""
import os
import threading

from dotenv import load_dotenv
from mysql.connector import Error, pooling

from src.database.exceptions import translate_mysql_error

load_dotenv()

DEFAULT_DATABASES = {
    "staging": "employee_staging",
    "oltp": "employee_oltp",
    "dw": "employee_dw",
}


class DatabaseConnection:

    _instances = {}                       # class -> its single instance
    _instances_lock = threading.Lock()
    _pools = {}                           # database name -> pool (shared)
    _pools_lock = threading.Lock()

    def __new__(cls):
        with DatabaseConnection._instances_lock:
            instance = DatabaseConnection._instances.get(cls)
            if instance is None:
                instance = super().__new__(cls)
                DatabaseConnection._instances[cls] = instance
        return instance

    def __init__(self):
        # __init__ runs on every DatabaseConnection() call; configure only once
        if getattr(self, "_configured", False):
            return

        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        try:
            self.port = int(os.getenv("DB_PORT", 3306))
            self.pool_size = int(os.getenv("DB_POOL_SIZE", 5))
        except ValueError:
            raise ValueError("DB_PORT and DB_POOL_SIZE must be valid numbers")

        if not self.host:
            raise ValueError("DB_HOST is missing in .env")
        if not self.user:
            raise ValueError("DB_USER is missing in .env")
        if not self.password:
            raise ValueError("DB_PASSWORD is missing in .env")
        if not 1 <= self.pool_size <= 32:
            raise ValueError("DB_POOL_SIZE must be between 1 and 32")

        # Optional: path to a CA bundle, needed by most cloud MySQL providers
        self.ssl_ca = os.getenv("DB_SSL_CA") or None

        self._configured = True

    # ---------- database names ----------
    @staticmethod
    def database_for(kind):
        """Resolve 'oltp' | 'dw' | 'staging' to the configured database name."""
        if kind not in DEFAULT_DATABASES:
            raise ValueError(f"Unknown database kind: {kind}")
        return os.getenv(f"DB_{kind.upper()}") or DEFAULT_DATABASES[kind]

    # ---------- pooling ----------
    def _pool_for(self, database_name):
        with DatabaseConnection._pools_lock:
            pool = DatabaseConnection._pools.get(database_name)
            if pool is None:
                config = {
                    "host": self.host,
                    "port": self.port,
                    "user": self.user,
                    "password": self.password,
                    "database": database_name,
                }
                if self.ssl_ca:
                    config["ssl_ca"] = self.ssl_ca
                    config["ssl_verify_cert"] = True
                pool = pooling.MySQLConnectionPool(
                    pool_name=f"pool_{database_name}",
                    pool_size=self.pool_size,
                    pool_reset_session=True,
                    **config,
                )
                DatabaseConnection._pools[database_name] = pool
        return pool

    def get_connection(self, database_name):
        """Borrow a connection; call .close() to give it back to the pool."""
        try:
            return self._pool_for(database_name).get_connection()
        except Error as err:
            raise translate_mysql_error(err) from err

    def ping(self, database_name):
        """True if a trivial query succeeds. Handy for a UI health banner."""
        connection = None
        try:
            connection = self.get_connection(database_name)
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Error:
                    pass

    @classmethod
    def _reset_for_tests(cls):
        """Forget all singletons and pools. For unit tests only."""
        with DatabaseConnection._instances_lock:
            DatabaseConnection._instances.clear()
        with DatabaseConnection._pools_lock:
            DatabaseConnection._pools.clear()