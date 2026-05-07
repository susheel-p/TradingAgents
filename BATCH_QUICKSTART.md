# Daily Batch Analysis Quick Start

Analyze 10 stocks every morning with **one preset configuration**.

## Setup (One-time)

```bash
tradingagents batch --setup-only
```

This creates:
- **Preset file:** `~/.tradingagents/daily_preset.json` — your LLM models, language, depth
- **Stocks file:** `stocks_today.txt` — your daily list of 10 stocks

## Daily Workflow

### Step 1: Edit the Preset (Optional)
Edit `~/.tradingagents/daily_preset.json` to set:
- `llm_provider` — OpenAI, Anthropic, Ollama, etc.
- `deep_think_llm` — reasoning/decision agent model
- `shallow_thinker` — analyst agent model  
- `output_language` — English, Spanish, French, etc.
- `research_depth` — debate rounds (1-3)
- `analysts` — which analysts to run (market, social, news, fundamentals)

Example:
```json
{
  "output_language": "English",
  "llm_provider": "anthropic",
  "shallow_thinker": "claude-opus-4-6",
  "deep_thinker": "claude-opus-4-6",
  "backend_url": null,
  "research_depth": 2,
  "analysts": ["market", "fundamentals"]
}
```

### Step 2: Update Your Stocks List
Edit `stocks_today.txt` — one ticker per line, or comma-separated:

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

### Step 3: Run Batch Analysis
```bash
tradingagents batch
```

Or with custom files/date:
```bash
tradingagents batch my_stocks.txt --preset my_preset.json --date 2026-05-06
```

## Output Structure

Reports saved to: `~/.tradingagents/logs/daily/{YYYY-MM-DD}/{TICKER}/`

```
daily/
  2026-05-06/
    AAPL/
      reports/
        market_report.md
        sentiment_report.md
        ...
      complete_report.md
      message_tool.log
    MSFT/
      ...
```

## Options

```
tradingagents batch STOCKS_FILE
  --preset FILE         Use custom preset (default: ~/.tradingagents/daily_preset.json)
  --date YYYY-MM-DD     Analysis date (default: today)
  --checkpoint          Resume from last checkpoint if interrupted
  --setup-only          Only create sample files, don't run
```

## Tips

1. **Comments in stocks file:** Lines starting with `#` are ignored
   ```
   # Tech stocks
   AAPL
   MSFT
   ```

2. **Multiple stocks formats:** Mix and match
   ```
   AAPL, MSFT
   GOOGL
   TSLA, AMZN, NVDA
   ```

3. **Save time:** Set `research_depth: 1` for quick runs, `2-3` for deeper analysis

4. **Language:** Change `output_language` for reports in different languages

5. **Check logs:** Each run creates a `message_tool.log` with all agent interactions

## Troubleshooting

**Stocks file not found:**
```bash
# Create stocks file in current directory
tradingagents batch --setup-only
```

**Want to use a different preset:**
```bash
# Copy the default and modify
cp ~/.tradingagents/daily_preset.json my_config.json
# Edit my_config.json
tradingagents batch stocks_today.txt --preset my_config.json
```

**Resume interrupted batch:**
```bash
tradingagents batch stocks_today.txt --checkpoint
```

## Monitor Your Batch Runs

All batch analyses are automatically logged. View them in the **Activity Dashboard**:

```bash
# Launch dashboard (requires Streamlit)
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501` — shows:
- All batch runs today
- Agent timelines and performance
- Token usage and costs
- Decision history and trends

Database: `~/.tradingagents/activity.db` (auto-created)
