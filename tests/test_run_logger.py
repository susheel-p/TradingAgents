"""Tests for RunLogger activity tracking."""

import tempfile
from pathlib import Path
import json

import pytest

from tradingagents.graph.run_logger import RunLogger


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_activity.db"
        yield db_path


def test_run_logger_creation(temp_db):
    """Test that RunLogger creates database and tables."""
    logger = RunLogger(temp_db)
    assert temp_db.exists()


def test_start_run(temp_db):
    """Test starting a run returns a UUID."""
    logger = RunLogger(temp_db)
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=["market", "news"],
        research_depth=1,
        source="cli",
    )

    assert run_id
    assert len(run_id) == 32  # UUID hex format
    assert isinstance(run_id, str)


def test_agent_events(temp_db):
    """Test recording agent start and complete events."""
    logger = RunLogger(temp_db)
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=["market"],
        research_depth=1,
    )

    # Record agent events
    logger.record_agent_start(run_id, "Market Analyst", "Analyst Team")
    logger.record_agent_complete(run_id, "Market Analyst", "Analyst Team")

    # Verify with direct DB query
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM agent_events WHERE run_id = ? AND agent_name = ?",
        (run_id, "Market Analyst"),
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 2  # One start, one complete


def test_save_report(temp_db):
    """Test saving agent reports."""
    logger = RunLogger(temp_db)
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=["market"],
        research_depth=1,
    )

    content = "This is a test market report with some content."
    logger.save_report(run_id, "Market Analyst", "market_report", content)

    # Verify with direct DB query
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content, word_count FROM agent_reports WHERE run_id = ? AND report_key = ?",
        (run_id, "market_report"),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == content
    assert row[1] == 9  # Word count


def test_token_snapshots(temp_db):
    """Test token snapshot recording."""
    logger = RunLogger(temp_db)
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=["market"],
        research_depth=1,
    )

    stats = {
        "llm_calls": 5,
        "tool_calls": 3,
        "tokens_in": 1000,
        "tokens_out": 500,
    }
    logger.snapshot_tokens(run_id, stats, current_agent="Market Analyst")

    # Verify with direct DB query
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT llm_calls, tokens_in, tokens_out FROM token_snapshots WHERE run_id = ?",
        (run_id,),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 5  # llm_calls
    assert row[1] == 1000  # tokens_in
    assert row[2] == 500  # tokens_out


def test_finish_run(temp_db):
    """Test finalizing a run."""
    logger = RunLogger(temp_db)
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=["market"],
        research_depth=1,
    )

    stats = {
        "llm_calls": 10,
        "tool_calls": 5,
        "tokens_in": 2000,
        "tokens_out": 1000,
    }
    logger.finish_run(
        run_id=run_id,
        final_decision="Buy",
        stats=stats,
        status="completed",
    )

    # Verify with direct DB query
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, final_decision, total_llm_calls, total_tokens_in, finished_at "
        "FROM runs WHERE run_id = ?",
        (run_id,),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "completed"  # status
    assert row[1] == "Buy"  # final_decision
    assert row[2] == 10  # total_llm_calls
    assert row[3] == 2000  # total_tokens_in
    assert row[4] is not None  # finished_at


def test_error_finish_run(temp_db):
    """Test finishing a run with error status."""
    logger = RunLogger(temp_db)
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=["market"],
        research_depth=1,
    )

    error_msg = "API rate limit exceeded"
    logger.finish_run(
        run_id=run_id,
        final_decision=None,
        stats={"llm_calls": 0, "tool_calls": 0, "tokens_in": 0, "tokens_out": 0},
        status="error",
        error_msg=error_msg,
    )

    # Verify with direct DB query
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, error_message FROM runs WHERE run_id = ?",
        (run_id,),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "error"
    assert error_msg in row[1]


def test_migrate_idempotent(temp_db):
    """Test that migrate() can be called multiple times safely."""
    logger = RunLogger(temp_db)
    logger.migrate()  # Call twice
    logger.migrate()  # Should not raise
    assert temp_db.exists()


def test_selected_analysts_json(temp_db):
    """Test that selected_analysts are stored as JSON."""
    logger = RunLogger(temp_db)
    analysts = ["market", "news", "social"]
    run_id = logger.start_run(
        ticker="SPY",
        analysis_date="2026-05-05",
        llm_provider="openai",
        deep_think_llm="gpt-4",
        quick_think_llm="gpt-3.5",
        selected_analysts=analysts,
        research_depth=1,
    )

    # Verify with direct DB query
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT selected_analysts FROM runs WHERE run_id = ?",
        (run_id,),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    stored_analysts = json.loads(row[0])
    assert stored_analysts == analysts
