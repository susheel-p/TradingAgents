"""Activity logger for TradingAgents runs. Captures events and outputs to SQLite."""

from __future__ import annotations

import datetime
import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any

_thread_local = threading.local()


class RunLogger:
    """Singleton-friendly activity logger to SQLite database."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize logger and create/migrate schema.

        Args:
            db_path: Path to SQLite database file. Created if missing.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def migrate(self) -> None:
        """Create all tables if they don't exist. Idempotent."""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id            TEXT PRIMARY KEY,
                    ticker            TEXT NOT NULL,
                    analysis_date     TEXT NOT NULL,
                    started_at        TEXT NOT NULL,
                    finished_at       TEXT,
                    status            TEXT NOT NULL DEFAULT 'running',
                    error_message     TEXT,
                    llm_provider      TEXT,
                    deep_think_llm    TEXT,
                    quick_think_llm   TEXT,
                    selected_analysts TEXT,
                    research_depth    INTEGER,
                    final_decision    TEXT,
                    duration_seconds  REAL,
                    total_llm_calls   INTEGER DEFAULT 0,
                    total_tool_calls  INTEGER DEFAULT 0,
                    total_tokens_in   INTEGER DEFAULT 0,
                    total_tokens_out  INTEGER DEFAULT 0,
                    source            TEXT NOT NULL DEFAULT 'cli'
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_runs_ticker_date
                ON runs(ticker, analysis_date)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_runs_started_at
                ON runs(started_at)
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_events (
                    event_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id           TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    agent_name       TEXT NOT NULL,
                    team             TEXT NOT NULL,
                    event_type       TEXT NOT NULL,
                    occurred_at      TEXT NOT NULL,
                    duration_seconds REAL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_events_run
                ON agent_events(run_id)
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_reports (
                    report_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id     TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    agent_name TEXT NOT NULL,
                    report_key TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    word_count INTEGER,
                    saved_at   TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_reports_run_key
                ON agent_reports(run_id, report_key)
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS token_snapshots (
                    snapshot_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id        TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    captured_at   TEXT NOT NULL,
                    llm_calls     INTEGER NOT NULL DEFAULT 0,
                    tool_calls    INTEGER NOT NULL DEFAULT 0,
                    tokens_in     INTEGER NOT NULL DEFAULT 0,
                    tokens_out    INTEGER NOT NULL DEFAULT 0,
                    current_agent TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_token_snapshots_run
                ON token_snapshots(run_id, captured_at)
                """
            )

            conn.commit()

    def start_run(
        self,
        ticker: str,
        analysis_date: str,
        llm_provider: str,
        deep_think_llm: str,
        quick_think_llm: str,
        selected_analysts: list[str],
        research_depth: int,
        source: str = "cli",
    ) -> str:
        """Start a new run and return its ID.

        Args:
            ticker: Stock ticker symbol.
            analysis_date: YYYY-MM-DD date.
            llm_provider: LLM provider name.
            deep_think_llm: Deep-thinking model name.
            quick_think_llm: Quick-thinking model name.
            selected_analysts: List of analyst types enabled.
            research_depth: Max debate rounds.
            source: 'cli' or 'programmatic'.

        Returns:
            run_id (UUID hex string).
        """
        run_id = uuid.uuid4().hex
        now = datetime.datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO runs (
                    run_id, ticker, analysis_date, started_at, status,
                    llm_provider, deep_think_llm, quick_think_llm,
                    selected_analysts, research_depth, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    ticker,
                    analysis_date,
                    now,
                    "running",
                    llm_provider,
                    deep_think_llm,
                    quick_think_llm,
                    json.dumps(selected_analysts),
                    research_depth,
                    source,
                ),
            )
            conn.commit()

        return run_id

    def record_agent_start(self, run_id: str, agent_name: str, team: str) -> None:
        """Record the start of an agent's work."""
        now = datetime.datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_events (run_id, agent_name, team, event_type, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, agent_name, team, "started", now),
            )
            conn.commit()

    def record_agent_complete(self, run_id: str, agent_name: str, team: str) -> None:
        """Record the completion of an agent's work. Computes duration vs start."""
        now = datetime.datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Get the start event
            cursor.execute(
                """
                SELECT occurred_at FROM agent_events
                WHERE run_id = ? AND agent_name = ? AND event_type = 'started'
                ORDER BY occurred_at DESC LIMIT 1
                """,
                (run_id, agent_name),
            )
            row = cursor.fetchone()
            duration_seconds = None
            if row:
                start_iso = row[0]
                start_dt = datetime.datetime.fromisoformat(start_iso)
                now_dt = datetime.datetime.fromisoformat(now)
                duration_seconds = (now_dt - start_dt).total_seconds()

            # Insert completion event
            cursor.execute(
                """
                INSERT INTO agent_events (run_id, agent_name, team, event_type, occurred_at, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, agent_name, team, "completed", now, duration_seconds),
            )
            conn.commit()

    def record_agent_error(
        self, run_id: str, agent_name: str, team: str, error_msg: str
    ) -> None:
        """Record an agent error."""
        now = datetime.datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_events (run_id, agent_name, team, event_type, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, agent_name, team, "error", now),
            )
            conn.commit()

    def snapshot_tokens(
        self, run_id: str, stats: dict[str, Any], current_agent: str | None = None
    ) -> None:
        """Record a token snapshot during streaming."""
        now = datetime.datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO token_snapshots
                (run_id, captured_at, llm_calls, tool_calls, tokens_in, tokens_out, current_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    now,
                    stats.get("llm_calls", 0),
                    stats.get("tool_calls", 0),
                    stats.get("tokens_in", 0),
                    stats.get("tokens_out", 0),
                    current_agent,
                ),
            )
            conn.commit()

    def save_report(
        self, run_id: str, agent_name: str, report_key: str, content: str
    ) -> None:
        """Save an agent's report text."""
        now = datetime.datetime.utcnow().isoformat()
        word_count = len(content.split()) if content else 0

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO agent_reports
                (run_id, agent_name, report_key, content, word_count, saved_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, agent_name, report_key, content, word_count, now),
            )
            conn.commit()

    def finish_run(
        self,
        run_id: str,
        final_decision: str | None,
        stats: dict[str, Any],
        status: str = "completed",
        error_msg: str | None = None,
    ) -> None:
        """Mark a run as finished. Computes duration and saves final stats."""
        now = datetime.datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Get start time to compute duration
            cursor.execute("SELECT started_at FROM runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            duration_seconds = None
            if row:
                start_iso = row[0]
                start_dt = datetime.datetime.fromisoformat(start_iso)
                now_dt = datetime.datetime.fromisoformat(now)
                duration_seconds = (now_dt - start_dt).total_seconds()

            # Update run with final state
            cursor.execute(
                """
                UPDATE runs SET
                    finished_at = ?,
                    status = ?,
                    error_message = ?,
                    final_decision = ?,
                    duration_seconds = ?,
                    total_llm_calls = ?,
                    total_tool_calls = ?,
                    total_tokens_in = ?,
                    total_tokens_out = ?
                WHERE run_id = ?
                """,
                (
                    now,
                    status,
                    error_msg,
                    final_decision,
                    duration_seconds,
                    stats.get("llm_calls", 0),
                    stats.get("tool_calls", 0),
                    stats.get("tokens_in", 0),
                    stats.get("tokens_out", 0),
                    run_id,
                ),
            )
            conn.commit()

            # Final token snapshot
            self.snapshot_tokens(run_id, stats, current_agent=None)

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local SQLite connection. Creates if missing."""
        if not hasattr(_thread_local, "conn") or _thread_local.conn is None:
            _thread_local.conn = sqlite3.connect(str(self.db_path))
        return _thread_local.conn

    def close(self) -> None:
        """Close thread-local connection if open."""
        if hasattr(_thread_local, "conn") and _thread_local.conn is not None:
            _thread_local.conn.close()
            _thread_local.conn = None
