"""BaseManager: shared plumbing for every data-access class.

Managers inherit from this (and therefore from DatabaseConnection, as the
brief requires) and stop repeating connect / try / rollback / close code.

    class ReviewManager(BaseManager):
        database_kind = "oltp"

        def get_review_by_id(self, review_id):
            row = self.fetch_one(
                "SELECT * FROM Performance_Reviews WHERE review_id = %s",
                (review_id,))
            return Review(**row) if row else None

Several statements that must succeed or fail together:

        with self.transaction() as cur:
            cur.execute(...)
            cur.execute(...)
        # committed here; rolled back automatically if anything raised
"""
import logging
from contextlib import contextmanager

from mysql.connector import Error

from src.database.db_manager import DatabaseConnection
from src.database.exceptions import DataAccessError, translate_mysql_error


class BaseManager(DatabaseConnection):

    database_kind = "oltp"        # override in subclasses: "oltp" | "dw"

    def __init__(self):
        super().__init__()
        self.database_name = self.database_for(self.database_kind)
        self.log = logging.getLogger(type(self).__name__)

    # ---------- transaction ----------
    @contextmanager
    def transaction(self, dictionary=False):
        """Yield a cursor. Commit on success, roll back on any error, and
        always hand the connection back to the pool."""
        connection = cursor = None
        try:
            connection = self.get_connection(self.database_name)
            cursor = connection.cursor(dictionary=dictionary)
            yield cursor
            connection.commit()
        except DataAccessError:
            self._rollback(connection)
            raise
        except Error as err:
            self._rollback(connection)
            self.log.error("Database error: %s", err)
            raise translate_mysql_error(err) from err
        except Exception:
            self._rollback(connection)
            raise
        finally:
            self._safe_close(cursor)
            self._safe_close(connection)

    # ---------- one-shot helpers ----------
    def fetch_all(self, sql, params=None):
        """Run a SELECT and return a list of dict rows."""
        with self.transaction(dictionary=True) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

    def fetch_one(self, sql, params=None):
        """Run a SELECT and return one dict row, or None."""
        with self.transaction(dictionary=True) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()

    def execute(self, sql, params=None):
        """Run INSERT/UPDATE/DELETE; return (rows_affected, last_insert_id)."""
        with self.transaction() as cursor:
            cursor.execute(sql, params or ())
            return cursor.rowcount, cursor.lastrowid

    # ---------- internals ----------
    def _rollback(self, connection):
        if connection is not None:
            try:
                connection.rollback()
            except Error:
                self.log.debug("Rollback failed (connection already closed)")

    def _safe_close(self, resource):
        if resource is not None:
            try:
                resource.close()
            except Error:
                self.log.debug("Close failed (already closed)")