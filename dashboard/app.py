"""Streamlit dashboard for TradingAgents activity tracking."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard import charts, db

st.set_page_config(
    page_title="TradingAgents Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🤖 TradingAgents Activity Dashboard")

# Initialize session state
if "selected_run_id" not in st.session_state:
    st.session_state.selected_run_id = None


def page_today_runs():
    """Today's Runs overview."""
    st.header("Today's Activity")

    runs_df = db.get_runs_today()

    if runs_df.empty:
        st.info("No runs recorded today.")
        return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Runs", len(runs_df))
    with col2:
        completed = len(runs_df[runs_df["status"] == "completed"])
        st.metric("Completed", completed)
    with col3:
        running = len(runs_df[runs_df["status"] == "running"])
        st.metric("Running", running, delta=None)
    with col4:
        errors = len(runs_df[runs_df["status"] == "error"])
        st.metric("Errors", errors, delta=None)

    st.subheader("Runs")

    # Display table with click handling
    display_df = runs_df[
        [
            "run_id",
            "ticker",
            "analysis_date",
            "status",
            "final_decision",
            "duration_seconds",
            "total_tokens_in",
            "total_tokens_out",
        ]
    ].copy()

    display_df["total_tokens_in"] = display_df["total_tokens_in"].fillna(0).astype(int)
    display_df["total_tokens_out"] = display_df["total_tokens_out"].fillna(0).astype(int)
    display_df["duration_seconds"] = (
        display_df["duration_seconds"].fillna(0).astype(int).astype(str) + "s"
    )
    display_df["total_tokens"] = (
        display_df["total_tokens_in"] + display_df["total_tokens_out"]
    ).astype(int)

    display_df = display_df[
        [
            "run_id",
            "ticker",
            "analysis_date",
            "status",
            "final_decision",
            "duration_seconds",
            "total_tokens",
        ]
    ]
    display_df.columns = [
        "Run ID",
        "Ticker",
        "Date",
        "Status",
        "Decision",
        "Duration",
        "Tokens",
    ]

    st.dataframe(display_df, use_container_width=True, key="runs_table")

    # Allow click to detail view
    if st.button("📊 View selected run details"):
        selected_idx = st.dataframe(display_df).index
        if selected_idx is not None and len(selected_idx) > 0:
            st.session_state.selected_run_id = runs_df.iloc[selected_idx[0]]["run_id"]
            st.rerun()


def page_run_detail():
    """Run detail: timeline and events."""
    st.header("Run Detail")

    run_id = st.selectbox(
        "Select Run",
        options=db.get_runs_today()["run_id"].tolist(),
        key="run_selector",
    )

    if not run_id:
        st.info("Select a run to view details.")
        return

    run_df = db.get_run_by_id(run_id)
    if run_df.empty:
        st.error("Run not found.")
        return

    run_row = run_df.iloc[0]

    # Run summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ticker", run_row["ticker"])
    with col2:
        st.metric("Date", run_row["analysis_date"])
    with col3:
        st.metric("Provider", run_row["llm_provider"])
    with col4:
        decision = run_row["final_decision"]
        color = (
            "🟢"
            if decision == "Buy"
            else (
                "🟡"
                if decision in ["Hold", "Overweight"]
                else ("🔴" if decision in ["Sell", "Underweight"] else "⚪")
            )
        )
        st.metric("Decision", f"{color} {decision}")

    st.divider()

    # Agent timeline
    st.subheader("Agent Timeline")
    agent_events_df = db.get_agent_events(run_id)

    if not agent_events_df.empty:
        gantt_fig = charts.build_gantt_chart(agent_events_df)
        st.plotly_chart(gantt_fig, use_container_width=True)

        st.subheader("Agent Events")
        display_events = agent_events_df[
            ["agent_name", "team", "event_type", "occurred_at", "duration_seconds"]
        ].copy()
        display_events.columns = ["Agent", "Team", "Event", "Time", "Duration (s)"]
        st.dataframe(display_events, use_container_width=True)
    else:
        st.info("No agent events recorded.")


def page_reports_viewer():
    """View agent reports."""
    st.header("Reports Viewer")

    all_runs = db.get_runs_today()
    if all_runs.empty:
        st.info("No runs to view.")
        return

    run_id = st.selectbox(
        "Select Run",
        options=all_runs["run_id"].tolist(),
        key="report_run_selector",
    )

    if not run_id:
        return

    reports_df = db.get_agent_reports(run_id)

    if reports_df.empty:
        st.info("No reports saved for this run.")
        return

    agent_names = reports_df["agent_name"].unique().tolist()
    selected_agent = st.selectbox("Select Agent", options=agent_names, key="agent_selector")

    agent_report = reports_df[reports_df["agent_name"] == selected_agent]
    if not agent_report.empty:
        report_row = agent_report.iloc[0]
        content = report_row["content"]
        word_count = report_row["word_count"]

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(content)
        with col2:
            st.metric("Words", word_count)
            st.metric("Saved", report_row["saved_at"][:10])

            st.download_button(
                label="📥 Download Report",
                data=content,
                file_name=f"{selected_agent}_{run_id[:8]}.md",
                mime="text/markdown",
            )


def page_token_usage():
    """Token usage charts."""
    st.header("Token Usage Analysis")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())

    runs_df = db.get_runs_by_date_range(
        start_date.isoformat(), end_date.isoformat()
    )

    if runs_df.empty:
        st.info("No runs in selected date range.")
        return

    # Per-run bar chart
    st.subheader("Tokens per Run")
    token_bar_fig = charts.build_token_bar_chart(runs_df)
    st.plotly_chart(token_bar_fig, use_container_width=True)

    # Single-run timeline
    st.subheader("Token Timeline (Select Run)")
    run_id = st.selectbox(
        "Run", options=runs_df["run_id"].tolist(), key="token_timeline_selector"
    )

    if run_id:
        token_timeline_df = db.get_token_timeline(run_id)
        if not token_timeline_df.empty:
            timeline_fig = charts.build_token_area_chart(token_timeline_df)
            st.plotly_chart(timeline_fig, use_container_width=True)
        else:
            st.info("No token snapshots for this run.")

    # Daily totals
    st.subheader("Daily Token Totals")
    daily_stats_df = db.get_daily_stats(days=int((end_date - start_date).days) or 30)
    if not daily_stats_df.empty:
        daily_line_fig = charts.build_daily_token_line(daily_stats_df)
        st.plotly_chart(daily_line_fig, use_container_width=True)

        st.dataframe(daily_stats_df, use_container_width=True)
    else:
        st.info("No daily stats available.")


def page_decision_history():
    """Decision history and performance."""
    st.header("Decision History")

    col1, col2 = st.columns(2)
    with col1:
        days_back = st.slider("Days Back", 1, 60, 30)
    with col2:
        ticker_filter = st.text_input("Filter by Ticker (optional)", "")

    decisions_df = db.get_decision_history(
        ticker=ticker_filter if ticker_filter else None, days=days_back
    )

    if decisions_df.empty:
        st.info("No decisions in selected range.")
        return

    # Distribution bar
    st.subheader("Decision Distribution")
    dist_fig = charts.build_decision_distribution_bar(decisions_df)
    st.plotly_chart(dist_fig, use_container_width=True)

    # Timeline scatter
    st.subheader("Decision Timeline")
    scatter_fig = charts.build_decision_scatter(decisions_df)
    st.plotly_chart(scatter_fig, use_container_width=True)

    # Decision table
    st.subheader("All Decisions")
    display_df = decisions_df[
        ["ticker", "analysis_date", "final_decision", "duration_seconds", "total_tokens"]
    ].copy()
    display_df.columns = ["Ticker", "Date", "Decision", "Duration (s)", "Tokens"]
    st.dataframe(display_df, use_container_width=True)

    # CSV export
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"decision_history_{datetime.now().isoformat()[:10]}.csv",
        mime="text/csv",
    )


def main():
    """Main app router."""
    pages = {
        "📊 Today's Runs": page_today_runs,
        "📈 Run Detail": page_run_detail,
        "📝 Reports": page_reports_viewer,
        "⚡ Token Usage": page_token_usage,
        "📑 Decision History": page_decision_history,
    }

    page = st.sidebar.radio("Navigation", options=list(pages.keys()))
    pages[page]()

    st.sidebar.divider()
    st.sidebar.write("**Database Location**")
    db_path = Path.home() / ".tradingagents" / "activity.db"
    if db_path.exists():
        st.sidebar.success(f"✅ {db_path}")
    else:
        st.sidebar.warning(f"⚠️ No activity DB found. Run analyses to create: {db_path}")


if __name__ == "__main__":
    main()
