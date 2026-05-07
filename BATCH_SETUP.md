# Daily Batch Analysis Setup Complete

I've implemented a new **batch analysis** feature for your daily workflow. No more configuring language, models, or date each time.

## What You Get

### 1. **Preset Configuration** (`~/.tradingagents/daily_preset.json`)
Set once, use forever. Stores:
- LLM provider (OpenAI, Anthropic, Ollama, etc.)
- Model names (shallow thinker for analysts, deep thinker for decisions)
- Language for reports
- Research depth (debate rounds)
- Which analysts to run

### 2. **Stocks List** (`stocks_today.txt`)
Update every morning with your 10 stocks:
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

### 3. **Batch Command**
Run all 10 stocks with one command:
```bash
tradingagents batch
```

## Quick Start (2 minutes)

### Step 1: Create preset and stocks files
```bash
tradingagents batch --setup-only
```

This creates:
- `~/.tradingagents/daily_preset.json` — LLM settings
- `stocks_today.txt` — sample stocks

### Step 2: Customize your preset
Edit `~/.tradingagents/daily_preset.json`:

```json
{
  "output_language": "English",
  "llm_provider": "anthropic",
  "deep_think_llm": "claude-opus-4-6",
  "shallow_thinker": "claude-opus-4-6",
  "backend_url": null,
  "research_depth": 1,
  "google_thinking_level": null,
  "openai_reasoning_effort": null,
  "anthropic_effort": null,
  "analysts": [
    "market",
    "social",
    "news",
    "fundamentals"
  ]
}
```

### Step 3: Update stocks list
Edit `stocks_today.txt` with your 10 stocks:
```
SPY
QQQ
AAPL
MSFT
GOOGL
AMZN
TSLA
NVDA
META
NFLX
```

### Step 4: Run batch analysis
```bash
tradingagents batch
```

That's it! All 10 stocks analyzed with your preset settings.

## Daily Routine

**Every morning:**
1. Edit `stocks_today.txt` with your 10 stocks
2. Run `tradingagents batch`
3. Check results in `~/.tradingagents/logs/daily/{DATE}/{TICKER}/`

**To customize for the day:**
- Change `output_language` in preset
- Adjust `research_depth` (1=quick, 2-3=thorough)
- Change `llm_provider` or models
- Edit `analysts` list (remove slow ones)

## Output Structure

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

## Features

✓ **Parallel preprocessing** — stocks are processed sequentially, reports organized by date
✓ **Preset persistence** — same config every day
✓ **Simple stocks file** — one ticker per line
✓ **Auto folder structure** — `daily/YYYY-MM-DD/{ticker}/`
✓ **Error handling** — skips failed stocks, continues with next
✓ **Activity logging** — timestamps, agent progress, token usage

## Advanced Usage

### Use different preset for a day
```bash
tradingagents batch stocks_today.txt --preset my_weekend_config.json
```

### Analyze a specific date
```bash
tradingagents batch stocks_today.txt --date 2026-05-05
```

### Resume if interrupted
```bash
tradingagents batch stocks_today.txt --checkpoint
```

### Create multiple presets
```bash
# Deep analysis (2 rounds, all analysts)
cp ~/.tradingagents/daily_preset.json deep_analysis.json
# Edit deep_analysis.json with research_depth: 2

# Quick analysis (1 round, key analysts only)
cp ~/.tradingagents/daily_preset.json quick_analysis.json
# Edit quick_analysis.json with research_depth: 1, analysts: ["market", "fundamentals"]
```

## Example Day

**Monday morning:**
1. Edit `stocks_today.txt`:
   ```
   AAPL
   MSFT
   GOOGL
   AMD
   NVDA
   ```

2. Run:
   ```bash
   tradingagents batch
   ```

3. Results saved to:
   ```
   ~/.tradingagents/logs/daily/2026-05-06/AAPL/complete_report.md
   ~/.tradingagents/logs/daily/2026-05-06/MSFT/complete_report.md
   ...
   ```

## Files Changed

- ✓ `cli/main.py` — added `batch` command
- ✓ `cli/preset.py` — new module for preset management
- ✓ Created: `~/.tradingagents/daily_preset.json`
- ✓ Created: `stocks_today.txt`

## Next Steps

1. Run `tradingagents batch --setup-only`
2. Edit the preset file with your preferred models
3. Update stocks_today.txt with your 10 stocks
4. Run `tradingagents batch` every morning!

See `BATCH_QUICKSTART.md` for more details and troubleshooting.
