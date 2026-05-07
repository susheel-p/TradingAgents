# Fundamentals Analysis Caching

**Run fundamentals analysis only when needed** — save time and API costs by caching results.

## Why Cache Fundamentals?

Fundamentals data changes slowly (quarterly earnings, balance sheet updates). Running it daily wastes:
- **Time:** 2-3 min per stock × 10 = 20-30 min daily
- **API costs:** Redundant calls to financial data providers
- **LLM tokens:** Reanalyzing unchanged data

**Solution:** Cache fundamentals and rerun only when beneficial.

## Configuration

Add to your preset (`~/.tradingagents/daily_preset.json`):

```json
{
  "fundamentals_frequency": "weekly",   // daily, weekly, monthly, never, always
  "fundamentals_day": "monday"           // If weekly, which day to run
}
```

## Options Explained

| Option | Behavior | Use Case |
|--------|----------|----------|
| **always** | Run fundamentals every day | Daily deep dives, when fundamentals matter most |
| **daily** | Run fundamentals once per day per stock | Stock-specific updates |
| **weekly** | Run on configured day (e.g., Monday) | Standard weekly check |
| **monthly** | Run once per month per stock | Long-term investors, cost savings |
| **never** | Skip fundamentals entirely | Quick analysis, market/sentiment only |

## Quick Examples

### Run Weekly (Monday)
```json
{
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "monday"
}
```

Every Monday, fundamentals run. Other days, analysts are: market, social, news.

### Run for New Stocks Only
```json
{
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "monday"
}
```

New stocks (never analyzed): fundamentals run on first analysis.
Existing stocks: fundamentals run only on configured day.

### Disable Fundamentals
```json
{
  "fundamentals_frequency": "never",
  "analysts": ["market", "social", "news"]
}
```

Fundamentals never run. Only market, social, news analysts.

### Always Run (Default for Quick Testing)
```json
{
  "fundamentals_frequency": "always"
}
```

Fundamentals run every time (legacy behavior).

## Cache Management

### View Cache
```bash
cat ~/.tradingagents/fundamentals_cache.json
```

Shows when each stock's fundamentals were last analyzed:
```json
{
  "AAPL": "2026-05-06",
  "MSFT": "2026-04-29",
  "GOOGL": "2026-05-06",
  "TSLA": "2026-04-28"
}
```

### Force Fundamentals Today
```bash
tradingagents batch --force-fundamentals
```

Override cache. Runs fundamentals for ALL stocks regardless of schedule.

### Clear Cache (Start Fresh)
```bash
rm ~/.tradingagents/fundamentals_cache.json
```

Next run treats all stocks as "new" — fundamentals run for all.

## Use Cases

### Case 1: Daily Quick Check (Market + Sentiment Only)
**Monday-Friday:** Skip fundamentals, focus on market/social trends
**Weekly:** Deep dive on Monday with fundamentals

```json
{
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "monday",
  "analysts": ["market", "social", "news"]  // Note: fundamentals removed
}
```

**Run each day:**
```bash
tradingagents batch
```

Result:
- Mon: All analysts including fundamentals
- Tue-Fri: Market, social, news only (3x faster)

### Case 2: New Stock Added Mid-Week
Stock not in cache → fundamentals run automatically on first analysis.

```bash
# Add NVDA to stocks_today.txt (never analyzed)
tradingagents batch

# Output shows:
# NVDA will run fundamentals (new stock)
# Existing stocks skip fundamentals (analyzed Monday)
```

### Case 3: CEO Earnings Announcement (Force Update)
Need fresh fundamentals despite weekly schedule:

```bash
# Force fundamentals for all stocks
tradingagents batch --force-fundamentals

# Or just update one stock manually
```

### Case 4: Monthly Investors
Fundamentals matter most, run once per month:

```json
{
  "fundamentals_frequency": "monthly",
  "analysts": ["market", "fundamentals"]
}
```

Fundamentals run ~30 days apart per stock.

## Batch Output Examples

### Weekly Schedule (Monday)
```
Batch Analysis Runner

+ 10 stocks loaded: AAPL, MSFT, GOOGL, TSLA, AMZN...
+ Analysis date: 2026-05-06
+ LLM Provider: ANTHROPIC
+ Output language: English
+ Fundamentals: Weekly
+   (on mondays)

[1/10] Analyzing AAPL...
[2/10] Analyzing MSFT...
[3/10] Analyzing GOOGL (skip fundamentals)...
[4/10] Analyzing TSLA (skip fundamentals)...
...
```

### Forced Fundamentals
```
+ Fundamentals: FORCED (all stocks)

[1/10] Analyzing AAPL...
[2/10] Analyzing MSFT...
```

### Disabled Fundamentals
```
+ Fundamentals: disabled

[1/10] Analyzing AAPL (skip fundamentals)...
```

## Cache Behavior

### First Run
- All stocks treated as "new" → fundamentals run
- Cache populated: `{"AAPL": "2026-05-06", ...}`

### Subsequent Runs (Same Day)
- Fundamentals cache NOT updated (same date)
- Fundamentals still skipped for cached stocks

### Next Week (Different Day)
- If weekly schedule: fundamentals skipped (not Monday yet)
- Cache NOT updated

### On Scheduled Day (e.g., Monday)
- Fundamentals run if > 7 days since last run
- Cache updated to new date

### New Stock Added
- Not in cache → fundamentals run
- Cache updated with today's date

## Advanced: Custom Schedules

### Monday and Friday
```bash
# Run batch on Monday with fundamentals
tradingagents batch

# Run batch on Friday with force flag
tradingagents batch --force-fundamentals
```

### Different Stocks, Different Schedules
```bash
# Tech stocks: weekly (Monday)
tradingagents batch tech_stocks.txt --preset tech_preset.json

# Energy stocks: monthly
tradingagents batch energy_stocks.txt --preset energy_preset.json
```

## Performance Impact

### Without Caching (Run Everything)
- 10 stocks × 8 analysts = ~50-100 min + token costs

### With Weekly Fundamentals
- Monday: ~50-100 min (all analysts)
- Tue-Fri: ~20-30 min (3 analysts, 4x faster)
- **Weekly avg:** ~20-30 min per day

### With Monthly Fundamentals
- Once per month: full analysis
- Other days: market + sentiment only
- **Monthly avg:** ~5-10 min per day

## Troubleshooting

### "Why did fundamentals run when they shouldn't?"
Check cache:
```bash
cat ~/.tradingagents/fundamentals_cache.json | grep TICKER_NAME
```

If cache is old, fundamentals runs based on frequency.

### "Cache has wrong dates"
```bash
# Reset cache
rm ~/.tradingagents/fundamentals_cache.json
# Next run rebuilds it
```

### "I want fundamentals on Tuesday, not Monday"
Edit preset:
```json
{
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "tuesday"
}
```

### "Force fundamentals, but skip for one stock"
Edit preset to remove fundamentals:
```json
{
  "fundamentals_frequency": "never",
  "analysts": ["market", "social", "news"]
}
```

Then run:
```bash
tradingagents batch
```

## Monitoring Cache Effectiveness

View token usage trends in the **Activity Dashboard** to see savings from fundamentals caching:

```bash
streamlit run dashboard/app.py
```

**Token Usage page shows:**
- Daily token consumption over time
- Cost trends (fundamentals days vs. non-fundamentals days)
- Per-run token breakdown by stock

Example patterns you'll see:
- **Monday** (fundamentals): High token count per stock
- **Tue-Fri** (no fundamentals): Lower token count (3-4x cheaper)
- **Weekly average:** ~70% of daily cost

---

## Summary

**Default behavior:** `weekly` on `monday`

**Configure in preset:**
```json
{
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "monday"
}
```

**Override today:**
```bash
tradingagents batch --force-fundamentals
```

**Monitor savings:**
```bash
streamlit run dashboard/app.py  # View token trends
```

**Result:**
- ✅ Fast daily runs (skip fundamentals)
- ✅ Deep weekly analysis (include fundamentals)
- ✅ New stocks auto-detected
- ✅ Lower API costs, fewer tokens
- ✅ Visible cost trends in dashboard

Done! Your fundamentals analysis is now smart and efficient.
