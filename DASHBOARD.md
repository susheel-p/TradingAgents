# TradingAgents Activity Dashboard

A complete activity tracking and visualization system for TradingAgents. Track all agent runs throughout the day, visualize agent timelines, token usage, and trading decisions with an interactive Streamlit dashboard.

## Quick Start

### Installation

```bash
# Install dashboard dependencies
pip install ".[dashboard]"
# or with uv
uv sync --extra dashboard
```

### Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open at `http://localhost:8501`

## Features

### 📊 Five Interactive Pages

#### **Today's Runs**
- Real-time metric cards: Total runs, Completed, Running, Failed
- Sortable table of today's analyses
- Quick drill-down to run details

#### **Run Detail**
- Agent execution timeline (Gantt chart)
- Breakdown of each agent's work period
- Full event log with durations
- Run summary: ticker, date, LLM provider, models used

#### **Reports Viewer**
- View full markdown reports from any agent
- Download reports as `.md` files
- Organized by agent type

#### **Token Usage**
- Per-run token consumption (stacked bar chart)
- In-run token timeline (area chart) showing token growth
- Daily aggregated token usage trends
- Cost estimation (rough approximation)

#### **Decision History**
- Decision distribution (how many Buy/Sell/Hold decisions)
- Timeline scatter plot (date × ticker × decision)
- Historical decision table with CSV export
- Session streaks (consecutive same-decision runs)

## Database Structure

All activity is persisted to SQLite at: `~/.tradingagents/activity.db`

### Tables

| Table | Purpose |
|---|---|
| `runs` | One row per CLI or programmatic analysis invocation |
| `agent_events` | Start/complete events for each agent (enables timeline) |
| `agent_reports` | Full markdown text output from each agent |
| `token_snapshots` | Periodic token counts during streaming (for timeline visualization) |

### Schema Highlights

- **One run ID per analysis**: UUID generated at start, propagated through all events
- **Agent-to-team mapping**: Agents grouped into 5 teams for color-coding
- **ISO-8601 timestamps**: Human-readable for direct DB inspection
- **Status tracking**: 'running' → 'completed' or 'error'

## How It Works

### Capture Phase (During CLI Analysis)

1. When you run `python -m cli.main analyze`, a new `run_id` is generated
2. Each agent's start and completion are logged as events
3. Reports are saved as they're generated
4. Token snapshots are captured every 5 streaming chunks
5. On completion, final stats and decision are recorded
6. On error, error message is logged with status='error'

### Storage Phase

All data is written to `activity.db` by the `RunLogger` class in `tradingagents/graph/run_logger.py`:

- Thread-safe using `threading.local()` connections (one per thread)
- Idempotent schema migration on first use
- No external dependencies beyond SQLite (built-in)

### Display Phase

The Streamlit app reads read-only from `activity.db`:

```python
from dashboard import db

# Get today's runs
runs_df = db.get_runs_today()

# Get agent timeline for a specific run
events_df = db.get_agent_events(run_id)

# Get token usage trends
daily_stats_df = db.get_daily_stats(days=14)
```

All queries return `pandas.DataFrame` for easy manipulation.

## Visualizations

### Agent Timeline (Gantt Chart)
- X-axis: Elapsed seconds from run start
- Y-axis: Agent names (sorted by execution order)
- Color: Team membership
- Hover: Agent name, duration, team

### Token Usage (Area + Line)
- Dual Y-axes: cumulative tokens (area) and LLM calls (line)
- X-axis: Elapsed seconds within run
- Useful for identifying which agents consume the most tokens

### Decision Scatter
- X-axis: Analysis date
- Y-axis: Ticker symbol
- Color: Decision (Buy/Sell/Hold/etc.) with semantic colors
- Size: Total tokens (larger dots = more expensive analysis)

### Daily Trends
- Token consumption over time
- Run count per day
- Average duration per day

## Data Retention

The activity database grows by ~50-100 KB per run (varies by model verbosity and number of agents selected).

For 10 runs/day × 365 days: ~180-365 MB/year

### Cleanup (Optional)

To remove old data:

```bash
# Delete all activity data
rm ~/.tradingagents/activity.db

# Partial cleanup: use sqlite3 directly
sqlite3 ~/.tradingagents/activity.db "DELETE FROM runs WHERE started_at < datetime('now', '-30 days');"
```

## Development

### Adding New Metrics

To track a new metric, add a column to the relevant table in `RunLogger.migrate()`:

```python
# In run_logger.py
cursor.execute("ALTER TABLE runs ADD COLUMN my_metric INTEGER DEFAULT 0")
```

Then write to it:

```python
logger.finish_run(..., my_metric=123)
```

Then read it in the dashboard:

```python
# In dashboard/db.py
def get_my_metrics(db_path=None) -> pd.DataFrame:
    return _read_sql("SELECT * FROM runs WHERE my_metric > 0", db_path)

# In dashboard/app.py
metrics_df = db.get_my_metrics()
st.dataframe(metrics_df)
```

### Adding New Pages

Create a new function in `dashboard/app.py`:

```python
def page_my_analysis():
    st.header("My Analysis")
    df = db.get_my_data()
    st.dataframe(df)
    st.plotly_chart(my_chart_function(df))

# Add to pages dict in main()
pages = {
    "📊 Today's Runs": page_today_runs,
    "🎯 My Analysis": page_my_analysis,  # <-- new
    ...
}
```

## Troubleshooting

### "No runs recorded"

The database might not exist yet. Run a full analysis first:

```bash
python -m cli.main analyze
```

This will create `~/.tradingagents/activity.db` and populate it.

### "Connection refused" or "database is locked"

Another process is writing to the DB. This is rare since each CLI run has its own connection via `threading.local()`. If it happens:

1. Wait for any running analyses to complete
2. Verify no background tasks are accessing the DB

### Charts show no data

Check:
1. Date range filter (in Token Usage / Decision History pages)
2. Ticker filter (if any)
3. Run status: charts only include completed runs (not running/error)

## Architecture Notes

### Why SQLite?

- **No setup needed**: Database is just a file, created on first use
- **Thread-safe**: Multiple CLI processes can write concurrently (one DB per ticker)
- **Queryable**: Inspect with `sqlite3` CLI or DB Browser for SQLite
- **Lightweight**: ~100 KB per 10 runs (no bloat)
- **Portable**: Backup/restore via simple file copy

### Why Streamlit?

- **Python-native**: Write dashboard in same language as CLI
- **Interactive**: Sliders, dropdowns, filters without frontend code
- **Built-in charts**: Plotly integration with minimal code
- **Hot-reload**: Edit and save; dashboard refreshes automatically
- **No containers needed**: Just `pip install streamlit && streamlit run app.py`

### Security Model

The dashboard is **read-only**. It opens the DB with `mode=ro` (read-only SQLite URI), meaning:
- No accidental writes from dashboard
- Concurrent reads are safe (no locking issues)
- Data integrity is protected

## Examples

### Query: "Which agents took the longest today?"

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("~/.tradingagents/activity.db")
df = pd.read_sql_query("""
    SELECT agent_name, team, SUM(duration_seconds) as total_seconds
    FROM agent_events
    WHERE DATE(occurred_at) = DATE('now') AND event_type = 'completed'
    GROUP BY agent_name
    ORDER BY total_seconds DESC
""", conn)
print(df)
```

### Query: "What was my average decision?"

```python
df = pd.read_sql_query("""
    SELECT final_decision, COUNT(*) as count, ROUND(AVG(duration_seconds)) as avg_duration_s
    FROM runs
    WHERE status = 'completed'
    GROUP BY final_decision
""", conn)
```

### Export: "Download all decisions for a ticker"

```python
df = pd.read_sql_query("""
    SELECT analysis_date, final_decision, duration_seconds, 
           total_tokens_in + total_tokens_out as total_tokens
    FROM runs
    WHERE ticker = 'SPY' AND status = 'completed'
    ORDER BY analysis_date DESC
""", conn)
df.to_csv("SPY_decisions.csv", index=False)
```

## Roadmap

Future enhancements:
- [ ] Multi-day comparison charts
- [ ] Performance metrics (alpha vs market)
- [ ] A/B testing dashboard (model A vs model B)
- [ ] Backtesting integration (realized returns per decision)
- [ ] Export to external observability (Prometheus, JSON, etc.)
- [ ] Dark mode theme

## Support

For issues or feature requests, open an issue on the project repo.

---

**Dashboard created with:** Streamlit + Plotly + SQLite + pandas
