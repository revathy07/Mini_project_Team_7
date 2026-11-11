# Streamlit app

Run from the repository root: `uv run streamlit run app/main.py`

- `main.py`: path setup, navigation, database health indicator.
- `data.py`: the only bridge between pages and managers. Returns cached DataFrames (`st.cache_data`) and wraps write operations, including warehouse sync.
- `views/`: one file per page. Pages contain no SQL and never call managers directly.

After any write that changes warehouse data, `data.py` clears the cache so dashboards show current numbers.