# Enterprise Employee Analytics & Data Warehouse

For the full project overview, database setup, data pipeline, and IAM details,
see the [project guide](./docs/README.md).

## Run locally

1. Install Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).
2. Copy `.env.example` to `.env`, then set the MySQL host, port, username, and
   password. The configured user must be able to access the staging, OLTP, and
   data warehouse databases.
3. Install dependencies and start the app:

   ```bash
   uv sync
   uv run streamlit run app/main.py
   ```

4. Open the local URL printed by Streamlit (normally
   `http://localhost:8501`).

## IAM and roles

The app uses local MySQL-backed accounts. On first setup, create the
`app_users` table and the initial administrator with:

```bash
uv run python -m src.auth.bootstrap_admin
```

The command prompts for the initial username, email, and a password of at
least 12 characters. It creates the account table with `CREATE TABLE IF NOT
EXISTS`; it does not drop or recreate any database. Run it against the OLTP
database configured in `.env`, using an account allowed to create tables.
Additional accounts are created by an administrator on the **User access**
page. There is no public registration.

| Role | Access |
| --- | --- |
| **Admin** | All dashboards and data-entry tools; create, update, deactivate, and reset user accounts. |
| **HR** | Dashboards; onboard employees, change employee details and managers, create projects, submit reviews, and sync the warehouse. |
| **Executive** | Read-only access to the analytical dashboards. |

Passwords are stored as salted scrypt hashes. Accounts are temporarily locked
after repeated failed sign-in attempts, and sessions expire after eight hours.
