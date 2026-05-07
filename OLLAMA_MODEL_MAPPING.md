# Ollama Model Mapping for TradingAgents

## Your Local Models

| Model | Size | VRAM | Notes |
|-------|------|------|-------|
| `gpt-oss:20b` | 13GB | ~14-16GB | Largest, best for complex reasoning |
| `qwen2.5-coder:7b` | 4.7GB | ~5-6GB | Coding-optimized, good tool use |
| `phi4-mini:latest` | 2.5GB | ~3-4GB | Lightweight, decent instruction following |
| `qwen3:4b` | 2.5GB | ~3-4GB | Lightweight general-purpose |
| `deepseek-r1:1.5b` | 1.1GB | ~2-3GB | Tiny, minimal reasoning |

---

## Agent Categories & Requirements

### 1. **Data Collection Analysts** (Tool-Calling Heavy)
**Agents:** Market Analyst, News Analyst, Fundamentals Analyst, Social Media Analyst

**Requirements:**
- Strong tool-use capability (bind_tools, follow structured tool calls)
- Good instruction following for complex prompts
- Detailed text generation for markdown tables & reports
- Moderate reasoning (selecting relevant indicators, interpreting data)

**✅ Recommended:** `qwen2.5-coder:7b` or `gpt-oss:20b`
- `qwen2.5-coder` excels at following detailed instructions and tool calls
- `gpt-oss:20b` handles complex multi-step tool chains better
- **Avoid:** `deepseek-r1:1.5b` (too small for reliable tool use)

---

### 2. **Debate Agents** (Reasoning & Argumentation)
**Agents:** Bull Researcher, Bear Researcher, Aggressive Debater, Conservative Debater, Neutral Debater

**Requirements:**
- Strong reasoning to build persuasive arguments
- Ability to synthesize multiple reports (market, fundamentals, sentiment, news)
- Generate conversational, engaging debate prose
- Handle debate history context (can be long)

**✅ Recommended:** `gpt-oss:20b` or `qwen2.5-coder:7b`
- `gpt-oss:20b` best for nuanced argument generation
- `qwen2.5-coder` handles this well but less sophisticated argumentation
- **Avoid:** `phi4-mini`, `qwen3:4b`, `deepseek-r1:1.5b` (insufficient reasoning depth)

---

### 3. **Decision Managers** (Structured Output, High Stakes)
**Agents:** Research Manager, Trader, Portfolio Manager

**Requirements:**
- **Critical:** Structured output adherence (ResearchPlan, TraderProposal, PortfolioDecision schemas)
  - Specific enum values (Buy/Overweight/Hold/Underweight/Sell)
  - Exact field names and descriptions
- Synthesis of all upstream analyst/debate context
- High-quality reasoning (investment decisions)
- Fallback to free-text markdown if structured output fails

**✅ Recommended:** `gpt-oss:20b` (primary), fallback to `qwen2.5-coder:7b`
- `gpt-oss:20b` has the best chance of respecting schema constraints
- These are the highest-stakes decisions; use your largest model
- **Avoid:** Models < 7B (poor structured output compliance)

---

## Recommended Configuration

### Option 1: **Single Model (Simplest)**
Use `gpt-oss:20b` for all agents. It's your largest and most capable.

```python
# tradingagents/default_config.py
DEFAULT_CONFIG = {
    "llm_provider": "ollama",
    "deep_think_llm": "gpt-oss:20b",      # Debate, decision agents
    "quick_think_llm": "gpt-oss:20b",     # Analyst agents
    "backend_url": "http://localhost:11434",  # Ollama default endpoint
    ...
}
```

**Pros:**
- Simplest setup (one model ID to manage)
- Consistent behavior across all agents
- Best quality overall

**Cons:**
- Higher VRAM usage (always running 20B)
- Slower inference
- Least cost-efficient if running locally

---

### Option 2: **Tiered (Recommended if VRAM-Constrained)**
Use larger model for high-stakes decisions, smaller for analysts.

```python
DEFAULT_CONFIG = {
    "llm_provider": "ollama",
    "deep_think_llm": "gpt-oss:20b",      # Research Manager, Trader, Portfolio Manager
    "quick_think_llm": "qwen2.5-coder:7b", # Analysts, debaters
    "backend_url": "http://localhost:11434",
    ...
}
```

**How to implement:** Modify agent creation to check the decision type and call the appropriate model.

**Pros:**
- Balances quality (decisions) with speed (analysis)
- More VRAM-efficient than all-20B
- Agents still have solid instruction-following capability

**Cons:**
- More configuration complexity
- Requires code changes to route different models to different agents

---

### Option 3: **Lightweight (Experimental, Speed-Focused)**
```python
DEFAULT_CONFIG = {
    "llm_provider": "ollama",
    "deep_think_llm": "qwen2.5-coder:7b",  # Best lightweight option
    "quick_think_llm": "phi4-mini:latest",  # Fallback for high-volume tasks
    ...
}
```

**Pros:**
- Fastest inference
- Lowest VRAM requirement
- Good for testing workflows

**Cons:**
- **Structured output will frequently fail** (schemas not respected)
- Debate reasoning quality suffers
- Tool use may be unreliable

---

## Model-by-Model Analysis

### `gpt-oss:20b` ⭐ **Best Choice**
- ✅ Excellent tool-use compliance
- ✅ Strong structured output support (schema fields, enums)
- ✅ Best reasoning for debate arguments
- ✅ Handles long context well (debate history, multi-report synthesis)
- ❌ Highest VRAM / slowest inference
- **Best for:** Decision agents (Research Manager, Trader, Portfolio Manager), debate loops
- **Worst for:** Nothing—it's generalist

### `qwen2.5-coder:7b` ⭐ **Second Choice**
- ✅ Strong instruction following (optimized for code/structured tasks)
- ✅ Good tool-use support
- ✅ Decent structured output (usually respects enum values)
- ✅ Fast enough for multi-agent loops
- ⚠️ Reasoning less nuanced than 20B
- ⚠️ Debate generation may lack sophistication
- **Best for:** Data analysts (tool-calling), fallback decision agents
- **Avoid:** Debate loops if demanding high-quality arguments

### `phi4-mini:latest`
- ✅ Fast and lightweight
- ⚠️ Instruction following uneven
- ❌ Structured output unreliable (field names, enum values often wrong)
- ❌ Tool use inconsistent
- **Best for:** Testing workflows, low-stakes tasks
- **Avoid:** Decision agents, tool-calling analysts

### `qwen3:4b`
- Similar to `phi4-mini` but slightly better reasoning
- Not recommended for any critical path
- **Best for:** Lightweight testing only

### `deepseek-r1:1.5b`
- ✅ Tiny and very fast
- ❌ Unreliable for structured output
- ❌ Tool use will fail frequently
- ❌ Insufficient context window for debate history
- **Best for:** Throwaway experimentation
- **Avoid:** Production runs

---

## Setup Instructions

### 1. Check Ollama is Running
```powershell
ollama serve  # Run in terminal 1 if not already running
# Terminal 2:
ollama list   # Should show your models
```

### 2. Update `default_config.py`

Replace these lines:
```python
# OLD (uses OpenAI models)
"llm_provider": "ollama",
"deep_think_llm": "gpt-5.4",
"quick_think_llm": "gpt-5.4-mini",
```

With (Option 1 - Simplest):
```python
# NEW (uses local Ollama)
"llm_provider": "ollama",
"deep_think_llm": "gpt-oss:20b",
"quick_think_llm": "gpt-oss:20b",
"backend_url": "http://localhost:11434",  # Add this
```

### 3. Test the Setup
```bash
# Run a smoke test with ollama
python scripts/smoke_structured_output.py ollama
# or if that doesn't exist:
python -m cli.main  # and select ollama + gpt-oss:20b
```

---

## Expected Behavior

### With `gpt-oss:20b`
- **Analysts:** Detailed reports with markdown tables ✅
- **Debaters:** Sophisticated arguments with counter-points ✅
- **Decision agents:** Structured output mostly respects schema ✅
- **Speed:** ~5-30 sec per agent depending on context length
- **VRAM:** ~13-14 GB while running

### With `qwen2.5-coder:7b`
- **Analysts:** Good reports, sometimes missing indicators ⚠️
- **Debaters:** Decent arguments but less nuanced ⚠️
- **Decision agents:** Schema mostly followed, rare field errors ⚠️
- **Speed:** ~1-10 sec per agent
- **VRAM:** ~5-6 GB

---

## Fallback Strategy

If `gpt-oss:20b` is too slow for your workflow, use **Option 2 (Tiered)**:

1. **Decision agents** → `gpt-oss:20b` (high stakes, worth waiting for)
2. **Debate agents** → `qwen2.5-coder:7b` (secondary importance)
3. **Data analysts** → `qwen2.5-coder:7b` (tool use is reliable enough)

Or if you hit VRAM limits, drop analysts to `phi4-mini` (they're just data fetchers).

---

## FAQ

**Q: Can I use a model not in my list?**
A: Yes! To add `mistral:7b`, just pull it (`ollama pull mistral`) and update `default_config.py`.

**Q: What if structured output fails?**
A: The code falls back to free-text markdown (see `structured.py`). Debate output will still be readable but less structured.

**Q: Should I run all models at once or switch between them?**
A: If VRAM-constrained, load one at a time. Ollama will automatically unload the previous model and load the new one. **Switching between 20B and 7B takes ~10s**, but no manual restart needed.

**Q: Can I use GPU acceleration?**
A: Yes! Ollama detects NVIDIA/AMD GPUs automatically. Most 20B models run on 8GB VRAM with GPU.

**Q: What about temperature/context length tuning?**
A: Ollama uses defaults (temp=0.7). The code doesn't expose these yet; you'd need to modify `llm_clients/factory.py` to set them via the HTTP API.

