# Daily Trading Analysis Workflow

## Overview

Analyze your **10 stocks every morning** with **one preset configuration**. Set up once, run forever.

## Installation (One-Time Setup)

```bash
tradingagents batch --setup-only
```

This creates:
- **~/.tradingagents/daily_preset.json** — your LLM settings (copy saved here)
- **stocks_today.txt** — sample 10 stocks (in current directory)

## Daily Workflow (30 seconds to launch analysis)

### Morning: Update your stocks list
Edit `stocks_today.txt` with your 10 stocks:
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

### Run analysis
```bash
tradingagents batch
```

**That's it!** Analysis runs with your preset settings (language, models, depth).

## Configuration: The Preset File

Located at: **~/.tradingagents/daily_preset.json**

Edit this ONCE to customize everything:

```json
{
  "output_language": "English",           # Reports in this language
  "llm_provider": "anthropic",            # openai, anthropic, ollama, google, etc.
  "deep_think_llm": "claude-opus-4-6",   # Reasoning agent (decisions)
  "shallow_thinker": "claude-opus-4-6",  # Analysis agent (analysts)
  "backend_url": null,                    # null = use provider default
  "research_depth": 1,                    # 1=quick, 2-3=thorough (debate rounds)
  "google_thinking_level": null,          # If using Google Gemini
  "openai_reasoning_effort": null,        # If using OpenAI o1/o3
  "anthropic_effort": null,               # If using Claude thinking
  "analysts": [
    "market",
    "social",
    "news",
    "fundamentals"
  ]
}
```

### Common Presets to Try

**Fast & Cheap (1-2 min per stock)**
```json
{
  "llm_provider": "anthropic",
  "deep_think_llm": "claude-haiku-4.5",
  "shallow_thinker": "claude-haiku-4.5",
  "research_depth": 1,
  "analysts": ["market", "fundamentals"]
}
```

**Deep Analysis (5-10 min per stock)**
```json
{
  "llm_provider": "anthropic",
  "deep_think_llm": "claude-opus-4-6",
  "shallow_thinker": "claude-opus-4-6",
  "research_depth": 2,
  "analysts": ["market", "social", "news", "fundamentals"]
}
```

**Local Ollama (free, but slower)**
```json
{
  "llm_provider": "ollama",
  "deep_think_llm": "phi4-mini:latest",
  "shallow_thinker": "phi4-mini:latest",
  "backend_url": "http://localhost:11434",
  "research_depth": 1,
  "analysts": ["market", "fundamentals"]
}
```

## Output Structure

Reports saved by date and stock:

```
~/.tradingagents/logs/daily/
├── 2026-05-06/           # Analysis date
│   ├── AAPL/
│   │   ├── reports/
│   │   │   ├── market.md
│   │   │   ├── sentiment.md
│   │   │   ├── news.md
│   │   │   └── fundamentals.md
│   │   ├── complete_report.md    # Full analysis
│   │   └── message_tool.log      # All agent interactions
│   ├── MSFT/
│   │   └── ...
│   └── ...
```

Each stock gets its own folder with:
- **complete_report.md** — full analysis report
- **reports/** — individual analyst reports
- **message_tool.log** — transcript of all agent interactions

## Command Reference

### Basic Run
```bash
# Use default preset and stocks_today.txt
tradingagents batch

# With custom stocks file
tradingagents batch my_stocks.txt

# With custom preset
tradingagents batch stocks_today.txt --preset my_config.json
```

### Advanced Options
```bash
# Analyze a specific date
tradingagents batch --date 2026-05-05

# Resume if interrupted (checkpoints enabled)
tradingagents batch --checkpoint

# Only create sample files, don't run
tradingagents batch --setup-only
```

### Create Multiple Presets
```bash
# Copy default to create variations
cp ~/.tradingagents/daily_preset.json deep_analysis.json
# Edit deep_analysis.json...
tradingagents batch stocks_today.txt --preset deep_analysis.json
```

## Use Cases

### Scenario 1: Quick Daily Check (5 stocks, 2 minutes)
```bash
# Edit stocks_today.txt: 5 stocks
# Edit ~/.tradingagents/daily_preset.json:
#   - "research_depth": 1
#   - "analysts": ["market", "fundamentals"]
#   - "shallow_thinker": "claude-haiku-4.5"

tradingagents batch
```

### Scenario 2: Weekend Deep Dive (10 stocks, 1 hour)
```bash
# Create weekend preset
cp ~/.tradingagents/daily_preset.json weekend_analysis.json
# Edit weekend_analysis.json:
#   - "research_depth": 3
#   - "analysts": ["market", "social", "news", "fundamentals"]
#   - "deep_think_llm": "claude-opus-4-6"

# Update stocks and run
tradingagents batch stocks_today.txt --preset weekend_analysis.json
```

### Scenario 3: Multi-Language Reports
```bash
# French reports
cp ~/.tradingagents/daily_preset.json french_preset.json
# Edit: "output_language": "French"
tradingagents batch stocks_today.txt --preset french_preset.json
```

## Troubleshooting

### "Stocks file not found"
```bash
# Make sure stocks_today.txt exists in current directory
tradingagents batch --setup-only
# This creates stocks_today.txt in current directory
```

### Change preset location
```bash
# Use absolute path
tradingagents batch --preset /path/to/my_preset.json

# Or relative path
tradingagents batch --preset ./presets/my_config.json
```

### Stocks file format notes
- One ticker per line: `AAPL`
- Comma-separated: `AAPL, MSFT, GOOGL`
- Comments with #: `# Tech stocks\nAAPL\nMSFT`
- Mixed formats work fine

### Resume a batch
```bash
# If batch interrupted, resume from last completed stock
tradingagents batch stocks_today.txt --checkpoint
```

## Performance Tips

1. **Reduce depth for speed:**
   - `research_depth: 1` = ~2-3 min per stock
   - `research_depth: 2` = ~5-10 min per stock

2. **Limit analysts for speed:**
   - Instead of all 4, use: `["market", "fundamentals"]`

3. **Use faster models:**
   - Haiku instead of Opus (Anthropic)
   - Phi4-mini instead of Phi4 (Ollama)

4. **Parallel processing:**
   - Stocks run sequentially, but you can run multiple batches in separate terminals

## Examples

### Example 1: Every Morning
```bash
# Morning: update stocks
vim stocks_today.txt
# Add your 10 stocks

# Launch analysis
tradingagents batch

# Results in ~/.tradingagents/logs/daily/$(date +%Y-%m-%d)/
```

### Example 2: Different Presets for Different Days
```bash
# Monday: Deep analysis
tradingagents batch stocks_today.txt --preset deep_preset.json

# Friday: Quick check
tradingagents batch stocks_today.txt --preset quick_preset.json

# Weekend: Comprehensive
tradingagents batch stocks_today.txt --preset weekend_preset.json
```

### Example 3: Organize by Market
```bash
# Tech stocks
tradingagents batch tech_stocks.txt

# Energy stocks
tradingagents batch energy_stocks.txt

# Healthcare stocks
tradingagents batch healthcare_stocks.txt
```

## Files Created

- `~/.tradingagents/daily_preset.json` — your preset configuration
- `stocks_today.txt` — your daily stocks list (current directory)
- `~/.tradingagents/logs/daily/{DATE}/{TICKER}/` — analysis results

## Summary

1. Run `tradingagents batch --setup-only` once
2. Edit `~/.tradingagents/daily_preset.json` with your settings
3. Every morning: edit `stocks_today.txt`, run `tradingagents batch`
4. Find reports in `~/.tradingagents/logs/daily/{DATE}/{TICKER}/`

Done! Analyze 10 stocks daily with one preset config.
