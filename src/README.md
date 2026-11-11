# Source code

| Package | Responsibility |
|---|---|
| `synthesizer/` | Scales the IBM dataset to 100K+ rows and generates projects, assignments, reviews and SCD2 history. One generator class per table; seeded for reproducibility. |
| `etls/` | `load_staging` (CSV to staging), `run_oltp_load`, `run_dim_employee`, `run_dw_etl`. Each runs stored procedures and then reconciliation checks. |
| `database/` | `DatabaseConnection` (per-class Singleton, pooling), `BaseManager` (transactions, fetch/execute helpers), `exceptions` (`DataAccessError` family). |
| `entities/` | `Employee`, `Project`, `Review`: attributes, validation, small behaviours. |
| `managers/` | Data access layer. `EmployeeManager`, `ProjectManager`, `ReviewManager` (OLTP); `AnalyticsManager` (warehouse); `OltpAnalyticsManager` (attrition and allocation); `WarehouseSync` (incremental warehouse refresh). |