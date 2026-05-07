# Daily Batch Analysis - Complete Setup Guide

## What You Have Now

✅ **Preset Configuration System**
- Store LLM settings, language, depth once in `~/.tradingagents/daily_preset.json`
- No more configuration prompts each run

✅ **Batch Analysis Command**
- Analyze 10+ stocks with one command: `tradingagents batch`
- All stocks use your preset settings
- Results organized by date: `~/.tradingagents/logs/daily/YYYY-MM-DD/TICKER/`

✅ **Smart Fundamentals Caching**
- Run fundamentals weekly (or custom schedule)
- New stocks auto-detected
- Skip redundant analyses, save time and API costs
- Override anytime with `--force-fundamentals`

---

## Quick Start (2 Minutes)

### Step 1: Create Default Files
```bash
tradingagents batch --setup-only
```

Creates:
- `~/.tradingagents/daily_preset.json` — your settings
- `stocks_today.txt` — sample 10 stocks

### Step 2: Customize Preset
Edit `~/.tradingagents/daily_preset.json`:

```json
{
  "llm_provider": "anthropic",           // openai, anthropic, ollama, google
  "deep_think_llm": "claude-opus-4-6",  // reasoning agent
  "shallow_thinker": "claude-opus-4-6", // analyst agents
  "output_language": "English",          // english, spanish, french, etc
  "research_depth": 1,                   // 1=quick, 2-3=thorough
  "analysts": [
    "market",
    "social",
    "news",
    "fundamentals"
  ],
  "fundamentals_frequency": "weekly",    // daily, weekly, monthly, never, always
  "fundamentals_day": "monday"           // which day for weekly
}
```

### Step 3: Add Your Stocks
Edit `stocks_today.txt`:
```
AAPL
MSFT
GOOGL
TSLA
AMZN
NVDA
META
NFLX
INTEL
AMD
```

### Step 4: Run!
```bash
tradingagents batch
```

That's it! All 10 stocks analyze with your preset.

---

## Daily Workflow

**Every morning:**
1. Update `stocks_today.txt` with your 10 stocks
2. Run `tradingagents batch`
3. Check results in `~/.tradingagents/logs/daily/$(date +%Y-%m-%d)/`

**To customize preset for today:**
- Change `output_language` in preset
- Adjust `research_depth` (1=quick, 2-3=thorough)
- Switch `llm_provider` or models
- Edit `analysts` list

---

## Key Features

### 1. Preset Configuration
Set once, use forever. Contains:
- LLM provider (OpenAI, Anthropic, Ollama, Google, etc.)
- Model names (shallow thinker for analysts, deep thinker for decisions)
- Language (English, Spanish, French, etc.)
- Research depth (1-3 debate rounds)
- Which analysts to run (market, social, news, fundamentals)

### 2. Smart Fundamentals Caching
**Why?** Fundamentals don't change daily, but take 2-3 min per stock.

**How it works:**
- Cache tracks when fundamentals last ran for each stock
- Run fundamentals weekly (or on custom schedule)
- New stocks auto-detected and analyzed immediately
- Skip redundant analyses, save time and API costs

**Configure:**
```json
{
  "fundamentals_frequency": "weekly",  // or daily, monthly, never, always
  "fundamentals_day": "monday"         // if weekly, which day
}
```

**Override:**
```bash
tradingagents batch --force-fundamentals  # Force all stocks today
```

### 3. Organized Output
```
~/.tradingagents/logs/daily/
  2026-05-06/
    AAPL/
      reports/
        market.md
        sentiment.md
        news.md
        fundamentals.md
      complete_report.md
      message_tool.log
    MSFT/
    ...
```

---

## Command Reference

### Basic Commands

```bash
# Run with default preset (same as before)
tradingagents batch

# Use custom stocks file
tradingagents batch my_stocks.txt

# Use custom preset
tradingagents batch stocks_today.txt --preset my_config.json

# Analyze specific date
tradingagents batch --date 2026-05-05

# Force fundamentals for all stocks
tradingagents batch --force-fundamentals

# Resume if interrupted (with checkpoints)
tradingagents batch --checkpoint
```

### Setup

```bash
# First time only
tradingagents batch --setup-only
```

---

## Examples

### Example 1: Fast Daily Check
**Goal:** Quick market + sentiment update, deep fundamentals on Monday

**Preset:**
```json
{
  "research_depth": 1,
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "monday"
}
```

**Run each day:**
```bash
tradingagents batch
```

**Result:**
- Monday: All analysts including fundamentals (50-100 min)
- Tue-Fri: Market, social, news only (20-30 min)

### Example 2: Comprehensive Analysis
**Goal:** Full analysis every day

**Preset:**
```json
{
  "research_depth": 2,
  "fundamentals_frequency": "always"
}
```

**Run:**
```bash
tradingagents batch
```

### Example 3: Different Presets for Different Days

**Monday (deep):**
```bash
tradingagents batch stocks_today.txt --preset deep_analysis.json
```

**Friday (quick):**
```bash
tradingagents batch stocks_today.txt --preset quick_analysis.json
```

---

## Files & Locations

### Created for You
- `~/.tradingagents/daily_preset.json` — your settings (in home dir)
- `stocks_today.txt` — your daily stocks (in current dir)
- `~/.tradingagents/fundamentals_cache.json` — when fundamentals last ran

### Analysis Results
- `~/.tradingagents/logs/daily/{DATE}/{TICKER}/` — reports for each stock

### Documentation
- `DAILY_WORKFLOW.md` — comprehensive workflow guide
- `BATCH_QUICKSTART.md` — quick reference
- `FUNDAMENTALS_CACHING.md` — detailed fundamentals guide
- `BATCH_SETUP.md` — initial setup instructions

---

## Frequently Asked Questions

### Q: Can I run fundamentals on a different day?
**A:** Edit preset:
```json
{
  "fundamentals_frequency": "weekly",
  "fundamentals_day": "friday"
}
```

### Q: What if I add a new stock mid-week?
**A:** New stocks automatically get fundamentals on first run (even if not scheduled).

### Q: How do I force fundamentals today?
**A:** 
```bash
tradingagents batch --force-fundamentals
```

### Q: Can I analyze different stocks with different settings?
**A:** Yes! Create multiple presets and use `--preset`:
```bash
tradingagents batch tech_stocks.txt --preset tech_preset.json
tradingagents batch energy_stocks.txt --preset energy_preset.json
```

### Q: How do I skip fundamentals entirely?
**A:** Set in preset:
```json
{
  "fundamentals_frequency": "never",
  "analysts": ["market", "social", "news"]
}
```

### Q: Will batch run if a stock fails?
**A:** Yes, it skips failed stocks and continues with the next one.

### Q: Can I save results to a custom folder?
**A:** Results auto-save to `~/.tradingagents/logs/daily/{DATE}/{TICKER}/`

### Q: How do I use a different language?
**A:** Edit preset:
```json
{
  "output_language": "Spanish"
}
```

---

## Monitor Your Batch Runs (Optional)

Every batch run is automatically logged to a SQLite database. View all your analyses, token usage, and decisions via the **Activity Dashboard**:

```bash
# Install dashboard (one-time)
pip install ".[dashboard]"

# Launch dashboard
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`

### Dashboard Features
- **Today's Runs** — all batch analyses from today
- **Run Detail** — agent timeline and breakdown for each stock
- **Reports Viewer** — view full markdown reports
- **Token Usage** — see token costs and trends
- **Decision History** — track Buy/Sell/Hold decisions over time

Example:
```bash
# After running batch
tradingagents batch
# Check results in dashboard
streamlit run dashboard/app.py
```

All data stored in: `~/.tradingagents/activity.db` (auto-created)

---

## Deploy on GPU (Optional: On-Demand Instances)

For cloud deployments (AWS Lambda, ECS, Google Cloud Run), **optionally** enable automatic backup of critical data to S3:

```bash
# Optional: enable S3 sync
export TRADINGAGENTS_S3_BUCKET="my-bucket"
tradingagents batch
```

**If S3_BUCKET is set, auto-syncs on exit:**
- Fundamentals cache (which stocks already analyzed)
- Dashboard database (history, token usage)

**If not set:** Batch runs normally (no sync).

**Benefit:** Prevents data loss if instance crashes or terminates.

See [GPU_DEPLOYMENT.md](GPU_DEPLOYMENT.md) for Lambda, ECS, Spot instances, and cost examples.

---

## Next Steps

1. Run `tradingagents batch --setup-only`
2. Edit `~/.tradingagents/daily_preset.json` with your settings
3. Edit `stocks_today.txt` with your 10 stocks
4. Run `tradingagents batch` every morning!
5. (Optional) Monitor runs with `streamlit run dashboard/app.py`

---

## Architecture

### File Structure
```
cli/
  main.py          # batch command added
  preset.py        # NEW: preset & cache management
  models.py        # existing
  utils.py         # existing

~/.tradingagents/
  daily_preset.json           # Your settings
  fundamentals_cache.json     # When fundamentals ran per stock

logs/
  daily/
    2026-05-06/
      AAPL/
      MSFT/
      ...
```

### Components Added
- `cli/preset.py` — Load presets, manage stocks, track fundamentals cache
- `batch` command in `cli/main.py` — Run multiple stocks with presets
- Fundamentals logic — Conditional analysis based on cache and frequency

---

## Troubleshooting

### Stocks file not found
```bash
# Recreate with default
tradingagents batch --setup-only
```

### Preset file not found
```bash
# Recreate with default
tradingagents batch --setup-only
# Then edit ~/.tradingagents/daily_preset.json
```

### Clear fundamentals cache (start fresh)
```bash
rm ~/.tradingagents/fundamentals_cache.json
```

### Check fundamentals cache
```bash
cat ~/.tradingagents/fundamentals_cache.json
```

### See batch command help
```bash
tradingagents batch --help
```

---

## Performance Tips

1. **Set `research_depth: 1`** for speed (no debate)
2. **Skip slow analysts** — remove from `analysts` list
3. **Use faster models** — Haiku over Opus
4. **Cache fundamentals** — set to `weekly` or `monthly`
5. **Skip fundamentals** — set frequency to `never`

---

## Summary

**Before:** Configure options every time, no fundamentals caching
**After:** 
- ✅ Preset configuration (set once, use forever)
- ✅ Batch analysis (10+ stocks in one command)
- ✅ Smart fundamentals (weekly, new stocks only, or force)
- ✅ Organized results (by date and ticker)
- ✅ Daily workflow (update stocks list, run batch)

Ready to go! 🚀
