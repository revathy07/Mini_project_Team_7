from src.database.base_manager import BaseManager
from src.database.exceptions import DataAccessError, WarehouseSyncError


class WarehouseSync(BaseManager):
    """Pushes OLTP changes into the warehouse. The only class the app uses
    to WRITE to the DW, and only through incremental procedures."""

    database_kind = "dw"

    def refresh_reviews(self):
        """Load reviews that are not in the fact table yet."""
        try:
            self.execute("CALL sp_load_fact_performance_incremental()")
        except DataAccessError as err:
            raise WarehouseSyncError(f"Warehouse refresh failed: {err}") from err

    def is_review_loaded(self, review_id):
        row = self.fetch_one(
            "SELECT 1 AS found FROM Fact_PerformanceReviews WHERE review_id = %s",
            (review_id,))
        return row is not None
    
    def refresh_employees(self, effective_date):
        """Run the incremental SCD2 proc: new hires get a first version,
        changed employees get a closed row + a new current row."""
        try:
            self.execute("CALL sp_load_dim_employee_scd2(%s)", (effective_date,))
        except DataAccessError as err:
            raise WarehouseSyncError(f"Warehouse refresh failed: {err}") from err

    def current_version_start(self, employee_code):
        """Start date of the current warehouse version, or None if not loaded."""
        row = self.fetch_one(
            "SELECT start_date FROM Dim_Employee "
            "WHERE employee_code = %s AND is_current = 1", (employee_code,))
        return row["start_date"] if row else None

    def version_history(self, employee_code):
        return self.fetch_all(
            "SELECT department_name, job_role, job_level, monthly_income, "
            "       start_date, end_date, is_current "
            "FROM Dim_Employee WHERE employee_code = %s ORDER BY start_date",
            (employee_code,))