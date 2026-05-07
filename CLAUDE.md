# TradingAgents Developer Guide

## Tech Stack
- **Python:** ≥ 3.10 (3.13 recommended)
- **Orchestration:** LangGraph (`StateGraph`, `SqliteSaver` checkpointing)
- **LLM providers:** LangChain wrappers — OpenAI, Anthropic, Google Gemini, xAI, DeepSeek, Qwen, GLM, Ollama, OpenRouter, Azure OpenAI
- **Data/finance:** yfinance, stockstats, backtrader, pandas
- **Structured output:** Pydantic `BaseModel` schemas
- **CLI:** Typer + Rich + questionary
- **Package manager:** pip or uv (lockfile present)

## Build & Run

```bash
# Install
pip install .
# or: uv sync

# Configure
cp .env.example .env          # fill in API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

# Run
tradingagents                 # CLI entry point
python -m cli.main            # or run from source

# Docker
docker compose run --rm tradingagents
```

## Testing

```bash
pytest                        # all tests
pytest -m unit                # fast, no external deps
pytest -m integration         # requires live API keys
pytest -m smoke               # quick sanity checks
```

Config in `pyproject.toml` under `[tool.pytest.ini_options]`. Test fixtures in `tests/conftest.py` stub all API keys so unit tests never need real credentials.

## Linting & Formatting

No enforced linter or formatter configured. Style is enforced by convention.

## Key Docs

- `README.md` — setup and user guide
- `CHANGELOG.md` — release history
- `tradingagents/agents/schemas.py` — Pydantic schemas with design notes
- `tradingagents/agents/utils/structured.py` — structured-output fallback logic
- `tradingagents/llm_clients/TODO.md` — provider roadmap

## Architecture

### Agent Pattern
Every agent is a closure returned by a `create_<name>(llm)` factory. No agent classes.

```python
def create_market_analyst(llm):
    def market_analyst_node(state):
        # ... LLM call + tools, return state mutation
        return {"messages": [...], "market_report": report}
    return market_analyst_node
```

### State Management
- **AgentState:** LangGraph `MessagesState` subclass
- **Sub-states:** embedded `TypedDict` dicts with `Annotated[type, "description"]` fields (e.g., `InvestDebateState`, `RiskDebateState`)
- See `tradingagents/agents/utils/agent_states.py`

### LLM Clients
- All inherit `BaseLLMClient` ABC (`tradingagents/llm_clients/base_client.py`)
- Instantiated via `factory.create_llm_client(provider, model, **kwargs)`
- OpenAI-compatible providers (xAI, DeepSeek, Qwen, GLM, Ollama, OpenRouter) reuse `OpenAIClient`
- Model catalog in `tradingagents/llm_clients/model_catalog.py`

### Vendor Routing
- Dispatch table in `tradingagents/dataflows/interface.py` (`VENDOR_METHODS`)
- Config keys in `DEFAULT_CONFIG["data_vendors"]` and `["tool_vendors"]` control which vendor is used
- Fallback chains built automatically; rate limit errors trigger next vendor in chain

### Structured Output
- Three decision agents use Pydantic schemas: `ResearchPlan`, `TraderProposal`, `PortfolioDecision`
- Helper in `tradingagents/agents/utils/structured.py` tries `llm.with_structured_output(schema)` at agent creation
- Falls back to free-text generation if provider doesn't support it
- Both paths render to same markdown shape so rest of pipeline is unchanged

### Data Flow
```
START
  → [Market, Social, News, Fundamentals] Analysts (parallel, tool-calling)
  → Bull ↔ Bear Researchers (debate loop)
  → Research Manager (structured: ResearchPlan)
  → Trader (structured: TraderProposal)
  → Aggressive ↔ Conservative ↔ Neutral Analysts (risk debate)
  → Portfolio Manager (structured: PortfolioDecision)
END
```

## Coding Conventions

- **Imports:** stdlib → third-party → local; use `from __future__ import annotations` in new files; lazy imports in `factory.py` to avoid heavy SDK loads at collection time
- **Docstrings:** single-line module docstrings; method docs in Google style (`Args:` / `Returns:`); not every function documented
- **Type hints:** used in `graph/` and `llm_clients/` layers; agent node closures loosely typed against state dicts
- **Classes:** agent logic is functional (closures), orchestration classes use standard patterns with typed methods

## Quick Links

- Graph setup: `tradingagents/graph/setup.py` → `tradingagents/graph/trading_graph.py`
- Agent factory: `tradingagents/llm_clients/factory.py`
- Config: `tradingagents/default_config.py`
- CLI: `cli/main.py`
