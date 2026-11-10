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