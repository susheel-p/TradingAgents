#!/usr/bin/env python
"""Batch analysis runner for multiple stocks from a JSON config."""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from tradingagents.graph.trading_graph import create_trading_graph
from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.default_config import DEFAULT_CONFIG

def load_config(config_file: str = "batch_analysis_config.json") -> dict:
    """Load batch analysis config from JSON file."""
    with open(config_file, "r") as f:
        return json.load(f)

def run_batch_analysis(config_file: str = "batch_analysis_config.json"):
    """Run analysis for all stocks in the config file."""
    config = load_config(config_file)
    analysis_config = config["analysis_config"]
    stocks = config["stocks"]

    # Create LLM client
    llm = create_llm_client(
        provider=analysis_config["llm_provider"],
        model=analysis_config["deep_think_llm"],
        backend_url=analysis_config.get("backend_url"),
    )

    # Create graph
    graph = create_trading_graph(llm)

    # Results directory
    results_dir = Path(DEFAULT_CONFIG["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = results_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    batch_dir.mkdir(exist_ok=True)

    print(f"\n📊 Batch Analysis Runner")
    print(f"📁 Results: {batch_dir}")
    print(f"🔧 Config: {analysis_config['deep_think_llm']}")
    print(f"📈 Stocks to analyze: {len(stocks)}\n")

    results_summary = []

    for i, stock_config in enumerate(stocks, 1):
        ticker = stock_config["ticker"]
        timeframe = stock_config["timeframe"]
        risk_pref = stock_config["risk_preference"]

        print(f"[{i}/{len(stocks)}] Analyzing {ticker} ({timeframe}, {risk_pref} risk)...")

        try:
            # Run graph
            input_state = {
                "ticker": ticker,
                "timeframe": timeframe,
                "risk_preference": risk_pref,
                "messages": [],
            }

            output = graph.invoke(input_state)

            # Save result
            result_file = batch_dir / f"{ticker}_result.json"
            with open(result_file, "w") as f:
                # Simplify output for JSON serialization
                json_output = {
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "risk_preference": risk_pref,
                    "final_decision": output.get("final_decision", "N/A"),
                    "status": "completed"
                }
                json.dump(json_output, f, indent=2)

            print(f"✅ {ticker}: Completed → {result_file}")
            results_summary.append({"ticker": ticker, "status": "✅ completed"})

        except Exception as e:
            print(f"❌ {ticker}: Error - {str(e)}")
            results_summary.append({"ticker": ticker, "status": f"❌ {str(e)[:50]}"})

    # Print summary
    print(f"\n{'='*60}")
    print("📋 Batch Summary:")
    for result in results_summary:
        print(f"  {result['ticker']:6} → {result['status']}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else "batch_analysis_config.json"
    run_batch_analysis(config_file)
