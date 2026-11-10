# Employee Analytics project guide

This project is a Streamlit employee analytics application backed by MySQL. It
includes a staging area, an operational (OLTP) database, and a star-schema
warehouse (OLAP). The current app includes role-based access control (IAM) for
dashboard and data-entry features.

## Current implementation branch

The IAM and Executive-role changes documented here are being developed on
`feature/executive-role`. This branch uses three application roles:
**Admin**, **HR**, and **Executive**. Executive is the read-only role that
matches the executive audience in the project statement; the earlier
Manager-specific role has been removed.

## Implemented functionality

- **Employee management:** HR and Admin users can onboard employees and update
  employee job details, including department, role, level, salary, and manager.
- **Project management:** HR and Admin users can create projects and browse
  project records.
- **SCD Type 2 history:** employee job changes retain effective-dated versions
  in the warehouse, preserving history instead of overwriting past values.
- **Performance reviews:** HR and Admin users can submit employee reviews.
- **Analytics:** the Streamlit app provides an overview plus Performance,
  Attrition, and Project bottleneck dashboards backed by the dimensional
  warehouse.
- **IAM:** users sign in with individual accounts. Admins can create accounts,
  assign roles, reset passwords, and deactivate/reactivate accounts. User
  registration is not public.

## Quick start

From the repository root:

```bash
uv sync
uv run streamlit run app/main.py
```

Open the local URL printed by Streamlit, normally
`http://localhost:8501`. Python 3.12 or newer, `uv`, and a reachable MySQL
server are required.

Configure `.env` using `.env.example`. Set `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, and, if needed, `DB_STAGING`, `DB_OLTP`, and `DB_DW`. Do not
commit `.env` or share its credentials. The app expects the database schemas
and data to be loaded before dashboards and operational pages can display
results.

For database creation and ETL instructions, see
[ETL pipeline guide](./ETL_pipeline_guide.md). For generated data design, see
[synthesis blueprint](./synthesis_blueprint.md).

## IAM and access

The app uses named, MySQL-backed accounts. There is no public registration.
Create the first administrator from the repository root:

```bash
uv run python -m src.auth.bootstrap_admin
```

The command prompts for a username, email, and password (at least 12
characters), then creates the `app_users` table in the configured OLTP
database if it does not exist. It does not drop or recreate databases. The
database account needs permission to create this table. An administrator
creates subsequent accounts from **User access** in the app.

| Role | Access |
| --- | --- |
| **Admin** | All dashboards and app tools; create accounts, assign roles, reset passwords, and deactivate/reactivate accounts. |
| **HR** | Analytics dashboards; onboard employees, change employee details and managers, create projects, submit reviews, and retry warehouse synchronization. |
| **Executive** | Read-only analytics dashboards: Overview, Performance, Attrition, and Project bottlenecks. |

This project uses Admin, HR, and Executive as its application roles. When an
existing IAM table is upgraded, legacy **Viewer** and **Manager** accounts are
automatically changed to **Executive** (read-only), and their optional
employee link is cleared. This keeps the removed Manager role from retaining
permissions or unexpectedly gaining HR write access.

Passwords are stored as salted scrypt hashes, not plaintext. Five consecutive
incorrect sign-in attempts temporarily lock an account for 15 minutes.
Sessions expire after eight hours. Deactivating an account prevents it from
signing in again.

## Project structure

- `app/main.py` — Streamlit entry point, sign-in screen, and role-based
  navigation.
- `app/views/` — dashboard and operational pages, including Admin-only user
  access management.
- `app/iam.py`, `src/auth/` — session checks, authentication, user management,
  permissions, and first-admin setup.
- `app/data.py` — app-facing data operations and permission checks for writes.
- `src/entities/`, `src/managers/`, `src/database/` — domain models, database
  operations, and MySQL access.
- `src/synthesizer/` — deterministic synthetic HR data generation.
- `src/etls/` — CSV staging, OLTP load, and warehouse ETL programs.
- `sql/` — staging, OLTP, warehouse, and ETL schema/procedure scripts.
- `data/raw/`, `data/processed/` — source and generated CSV datasets.
- `test/` — model, database-layer, IAM, and employee-history tests.

## Testing

Run the IAM tests:

```bash
uv run pytest -q test/test_iam.py
```

Run the focused model and employee-history tests:

```bash
uv run pytest -q test/test_iam.py test/test_employee.py test/test_project.py \
  test/test_review.py test/test_change_rules.py
```

Database integration tests may require a running MySQL server and the schemas
configured in `.env`.
