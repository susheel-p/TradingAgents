# TradingAgents Activity Dashboard — Quick Start (5 Minutes)

## Installation

```bash
# Install dashboard dependencies
pip install ".[dashboard]"
```

That's it! The RunLogger is integrated into the CLI automatically.

## Use It

### Step 1: Run an Analysis (as usual)
```bash
python -m cli.main analyze
```
Answer the prompts normally. Behind the scenes, all agent activities are being logged to `~/.tradingagents/activity.db`.

### Step 2: Launch the Dashboard
```bash
streamlit run dashboard/app.py
```

Your browser opens to http://localhost:8501 automatically.

### Step 3: Explore

**Page 1: Today's Runs**
- See metrics: total runs, completed, running, failed
- Click on any run to jump to its details
- Sortable table of today's analyses

**Page 2: Run Detail**
- Timeline showing when each agent was working
- Full breakdown of agent events with durations
- Run summary (ticker, date, models used, final decision)

**Page 3: Reports Viewer**
- Read the full markdown report from any agent
- Download as `.md` file for external use
- View word counts and save timestamps

**Page 4: Token Usage**
- Three charts: per-run tokens, in-run timeline, daily totals
- Spot which agents consume the most tokens
- Track token trends over 2 weeks

**Page 5: Decision History**
- Bar chart: how many Buy/Sell/Hold decisions overall
- Scatter plot: which stocks, which dates, which decisions
- Download decision history as CSV

## Real Example: 10 Runs a Day

Run analyses throughout the day as usual:

```bash
# 9 AM
python -m cli.main analyze  # SPY analysis

# 12 PM
python -m cli.main analyze  # AAPL analysis

# 3 PM
python -m cli.main analyze  # QQQ analysis

# ... repeat throughout the day ...
```

At end of day, launch the dashboard:

```bash
streamlit run dashboard/app.py
```

**Today's Runs page** shows all 10 runs:
- Metrics: 10 total, X completed, Y running, Z failed
- Table: each run's ticker, decision, duration, token count

**Decision History page** (set filter to "today"):
- Bar chart: distribution of your 10 decisions
- Scatter: each run plotted (date × ticker × decision color)
- CSV: export for analysis

**Token Usage page**:
- Bar chart: which run was most expensive
- Timeline: focus on a single run to see token consumption pattern
- Trends: daily total tokens across all 10 runs

## Database Location

All data is stored at:
```
~/.tradingagents/activity.db
```

This is a standard SQLite file. You can:
- Inspect directly: `sqlite3 ~/.tradingagents/activity.db`
- Backup: `cp ~/.tradingagents/activity.db ~/activity_backup.db`
- Delete: `rm ~/.tradingagents/activity.db` (starts fresh)

## Common Workflows

### "Show me all my Buy decisions from this week"
1. Open **Decision History** page
2. Drag date slider to last 7 days
3. Look at scatter plot and table
4. Download CSV if needed

### "Which agent took the longest today?"
1. Open **Run Detail** page
2. Select any run from the dropdown
3. View Gantt chart: agent bar heights show duration

### "Why did this run use so many tokens?"
1. Open **Token Usage** page
2. Find the run in the bar chart (tallest bar)
3. Select it in the "Token Timeline" section
4. View area chart: see which part of the run consumed tokens
5. Open **Run Detail** for that run
6. View **Reports** page to see what each agent generated

### "Export all my decisions for backtest analysis"
1. Open **Decision History** page
2. Set date range and ticker filters as needed
3. Click "📥 Download CSV" button
4. Use in your backtest tool

## Customization

### Change dashboard port
```bash
streamlit run dashboard/app.py --server.port 8502
```

### Share dashboard (optional - requires internet)
```bash
# First-time setup:
streamlit config set browser.gatherUsageStats false  # Skip telemetry
streamlit deploy  # Requires GitHub account

# Or use ngrok for temporary sharing:
# streamlit run dashboard/app.py & ngrok http 8501
```

### Query data directly (Python)
```python
from dashboard import db

# Today's runs
runs_today = db.get_runs_today()
print(runs_today[['ticker', 'final_decision', 'duration_seconds']])

# Buy decisions from last 14 days
buy_decisions = db.get_decision_history(days=14)
print(buy_decisions[buy_decisions['final_decision'] == 'Buy'])

# Tokens per run
runs = db.get_runs_by_date_range('2026-05-01', '2026-05-07')
print(runs[['ticker', 'total_tokens_in', 'total_tokens_out']])
```

## Stop the Dashboard

Press `Ctrl+C` in the terminal where you ran `streamlit run dashboard/app.py`.

## That's It!

You now have:
- ✅ Full tracking of every agent's activity
- ✅ Visual timelines and charts
- ✅ Token usage monitoring
- ✅ Decision history
- ✅ Ability to run 10x/day and review everything

No changes to your analysis scripts. Everything works automatically.

---

**For more details**, see:
- `DASHBOARD.md` — detailed user guide with examples
- `IMPLEMENTATION_SUMMARY.md` — technical architecture
- Database docs — check `~/.tradingagents/activity.db` schema directly
