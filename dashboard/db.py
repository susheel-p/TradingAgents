"""Read-only SQLite queries for activity dashboard."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def _get_db_path(db_path: Path | str | None = None) -> Path:
    """Resolve database path. Default: ~/.tradingagents/activity.db"""
    if db_path is None:
        db_path = Path.home() / ".tradingagents" / "activity.db"
    return Path(db_path)


def _read_sql(query: str, db_path: Path | str | None = None) -> pd.DataFrame:
    """Execute read-only query and return DataFrame."""
    db_path = _get_db_path(db_path)
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def get_runs_today(db_path: Path | str | None = None) -> pd.DataFrame:
    """Get all runs started today, most recent first."""
    query = """
    SELECT *
    FROM runs
    WHERE DATE(started_at) = DATE('now')
    ORDER BY started_at DESC
    """
    return _read_sql(query, db_path)


def get_runs_by_date_range(
    start: str, end: str, db_path: Path | str | None = None
) -> pd.DataFrame:
    """Get runs within date range (YYYY-MM-DD format)."""
    query = """
    SELECT *
    FROM runs
    WHERE DATE(started_at) >= DATE(?)
      AND DATE(started_at) <= DATE(?)
    ORDER BY started_at DESC
    """
    db_path = _get_db_path(db_path)
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df = pd.read_sql_query(query, conn, params=(start, end))
        conn.close()
        return df
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def get_agent_events(run_id: str, db_path: Path | str | None = None) -> pd.DataFrame:
    """Get all agent events for a run, ordered by time."""
    query = """
    SELECT *
    FROM agent_events
    WHERE run_id = ?
    ORDER BY occurred_at ASC
    """
    db_path = _get_db_path(db_path)
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df = pd.read_sql_query(query, conn, params=(run_id,))
        conn.close()
        return df
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def get_agent_reports(run_id: str, db_path: Path | str | None = None) -> pd.DataFrame:
    """Get all reports for a run."""
    query = """
    SELECT *
    FROM agent_reports
    WHERE run_id = ?
    ORDER BY saved_at ASC
    """
    db_path = _get_db_path(db_path)
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df = pd.read_sql_query(query, conn, params=(run_id,))
        conn.close()
        return df
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def get_token_timeline(
    run_id: str, db_path: Path | str | None = None
) -> pd.DataFrame:
    """Get token snapshots for a run (for timeline chart)."""
    query = """
    SELECT captured_at, llm_calls, tool_calls, tokens_in, tokens_out, current_agent
    FROM token_snapshots
    WHERE run_id = ?
    ORDER BY captured_at ASC
    """
    db_path = _get_db_path(db_path)
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df = pd.read_sql_query(query, conn, params=(run_id,))
        conn.close()
        return df
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def get_decision_history(
    ticker: str | None = None, days: int = 30, db_path: Path | str | None = None
) -> pd.DataFrame:
    """Get completed run decisions for past N days, optionally filtered by ticker."""
    if ticker:
        query = f"""
        SELECT
            run_id, ticker, analysis_date, final_decision, duration_seconds,
            (total_tokens_in + total_tokens_out) as total_tokens,
            started_at
        FROM runs
        WHERE status = 'completed'
          AND ticker = ?
          AND started_at >= datetime('now', '-{days} days')
        ORDER BY started_at DESC
        """
        db_path = _get_db_path(db_path)
        if not db_path.exists():
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            df = pd.read_sql_query(query, conn, params=(ticker,))
            conn.close()
            return df
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            return pd.DataFrame()
    else:
        query = f"""
        SELECT
            run_id, ticker, analysis_date, final_decision, duration_seconds,
            (total_tokens_in + total_tokens_out) as total_tokens,
            started_at
        FROM runs
        WHERE status = 'completed'
          AND started_at >= datetime('now', '-{days} days')
        ORDER BY started_at DESC
        """
        return _read_sql(query, db_path)


def get_daily_stats(days: int = 14, db_path: Path | str | None = None) -> pd.DataFrame:
    """Get daily aggregates: run count, total tokens, total duration."""
    query = f"""
    SELECT
        DATE(started_at) as date,
        COUNT(*) as runs,
        SUM(total_tokens_in + total_tokens_out) as total_tokens,
        SUM(duration_seconds) as total_duration_seconds
    FROM runs
    WHERE status = 'completed'
      AND started_at >= datetime('now', '-{days} days')
    GROUP BY DATE(started_at)
    ORDER BY date DESC
    """
    return _read_sql(query, db_path)


def get_run_by_id(run_id: str, db_path: Path | str | None = None) -> pd.DataFrame:
    """Get a single run by ID."""
    query = "SELECT * FROM runs WHERE run_id = ?"
    db_path = _get_db_path(db_path)
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df = pd.read_sql_query(query, conn, params=(run_id,))
        conn.close()
        return df
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()
