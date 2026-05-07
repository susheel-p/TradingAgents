"""Plotly chart builders for activity dashboard."""

from __future__ import annotations

import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


DECISION_COLORS = {
    "Buy": "#22c55e",
    "Overweight": "#86efac",
    "Hold": "#fbbf24",
    "Underweight": "#fca5a5",
    "Sell": "#ef4444",
}


def build_gantt_chart(agent_events_df: pd.DataFrame) -> go.Figure:
    """Build Gantt timeline of agent execution.

    Input DataFrame should have columns: agent_name, team, event_type, occurred_at, duration_seconds.
    """
    if agent_events_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No agent events recorded")
        return fig

    # Convert to datetime
    agent_events_df = agent_events_df.copy()
    agent_events_df["occurred_at"] = pd.to_datetime(agent_events_df["occurred_at"])

    # Compute start/finish times for each agent (pair of start/complete events)
    gantt_data = []
    for agent_name in agent_events_df["agent_name"].unique():
        agent_df = agent_events_df[agent_events_df["agent_name"] == agent_name].sort_values(
            "occurred_at"
        )
        start_rows = agent_df[agent_df["event_type"] == "started"]
        complete_rows = agent_df[agent_df["event_type"] == "completed"]

        if not start_rows.empty and not complete_rows.empty:
            start_time = start_rows.iloc[0]["occurred_at"]
            finish_time = complete_rows.iloc[0]["occurred_at"]
            team = complete_rows.iloc[0]["team"]

            gantt_data.append(
                {
                    "Task": agent_name,
                    "Team": team,
                    "Start": start_time,
                    "Finish": finish_time,
                }
            )

    if not gantt_data:
        fig = go.Figure()
        fig.add_annotation(text="No completed agent events")
        return fig

    gantt_df = pd.DataFrame(gantt_data)

    fig = px.timeline(
        gantt_df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Team",
        title="Agent Execution Timeline",
        labels={"Task": "Agent", "Team": "Team"},
    )
    fig.update_layout(height=400, showlegend=True)
    return fig


def build_token_area_chart(token_timeline_df: pd.DataFrame) -> go.Figure:
    """Build area chart of cumulative token usage over time within a run.

    Input: token_snapshots DataFrame with: captured_at, tokens_in, tokens_out, llm_calls.
    """
    if token_timeline_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No token snapshots")
        return fig

    token_timeline_df = token_timeline_df.copy()
    token_timeline_df["captured_at"] = pd.to_datetime(token_timeline_df["captured_at"])

    # Compute elapsed seconds from start
    min_time = token_timeline_df["captured_at"].min()
    token_timeline_df["elapsed_seconds"] = (
        token_timeline_df["captured_at"] - min_time
    ).dt.total_seconds()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=token_timeline_df["elapsed_seconds"],
            y=token_timeline_df["tokens_in"],
            name="Tokens In",
            fill="tozeroy",
            line=dict(color="#3b82f6"),
            hovertemplate="<b>Input Tokens</b><br>%{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=token_timeline_df["elapsed_seconds"],
            y=token_timeline_df["tokens_out"],
            name="Tokens Out",
            fill="tozeroy",
            line=dict(color="#f97316"),
            hovertemplate="<b>Output Tokens</b><br>%{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=token_timeline_df["elapsed_seconds"],
            y=token_timeline_df["llm_calls"],
            name="LLM Calls",
            line=dict(color="#8b5cf6", dash="dash"),
            yaxis="y2",
            hovertemplate="<b>LLM Calls</b><br>%{y}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Token Usage Over Time",
        xaxis_title="Elapsed Seconds",
        yaxis_title="Tokens",
        yaxis2=dict(title="LLM Calls", overlaying="y", side="right"),
        height=400,
        hovermode="x unified",
    )

    return fig


def build_token_bar_chart(runs_df: pd.DataFrame) -> go.Figure:
    """Build stacked bar chart of token usage per run.

    Input: runs DataFrame with ticker, analysis_date, total_tokens_in, total_tokens_out.
    """
    if runs_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No runs")
        return fig

    runs_df = runs_df.copy()
    runs_df["label"] = runs_df["ticker"] + "\n" + runs_df["analysis_date"].astype(str)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=runs_df["label"],
            y=runs_df["total_tokens_in"],
            name="Input Tokens",
            marker_color="#3b82f6",
            hovertemplate="<b>Input Tokens</b><br>%{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=runs_df["label"],
            y=runs_df["total_tokens_out"],
            name="Output Tokens",
            marker_color="#f97316",
            hovertemplate="<b>Output Tokens</b><br>%{y}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="stack",
        title="Token Usage Per Run",
        xaxis_title="Run",
        yaxis_title="Total Tokens",
        height=400,
        hovermode="x",
    )

    return fig


def build_decision_scatter(decisions_df: pd.DataFrame) -> go.Figure:
    """Build scatter plot of decisions by date and ticker.

    Input: decisions DataFrame with: analysis_date, ticker, final_decision, total_tokens, duration_seconds.
    """
    if decisions_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No decisions")
        return fig

    decisions_df = decisions_df.copy()
    decisions_df["analysis_date"] = pd.to_datetime(decisions_df["analysis_date"])

    # Map decision to color
    decisions_df["color"] = decisions_df["final_decision"].map(
        DECISION_COLORS
    ).fillna("#9ca3af")

    # Scale size: min 8, max 30
    if decisions_df["total_tokens"].max() > decisions_df["total_tokens"].min():
        size_min, size_max = 8, 30
        token_min = decisions_df["total_tokens"].min()
        token_max = decisions_df["total_tokens"].max()
        decisions_df["size"] = (
            (decisions_df["total_tokens"] - token_min)
            / (token_max - token_min)
            * (size_max - size_min)
            + size_min
        )
    else:
        decisions_df["size"] = 15

    fig = px.scatter(
        decisions_df,
        x="analysis_date",
        y="ticker",
        color="final_decision",
        size="size",
        title="Decision History",
        labels={
            "analysis_date": "Date",
            "ticker": "Ticker",
            "final_decision": "Decision",
        },
        color_discrete_map=DECISION_COLORS,
    )

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Date: %{x|%Y-%m-%d}<br>Decision: %{marker.color}<br>Tokens: %{customdata}<extra></extra>",
        customdata=decisions_df["total_tokens"],
    )

    fig.update_layout(height=400)
    return fig


def build_decision_distribution_bar(decisions_df: pd.DataFrame) -> go.Figure:
    """Build bar chart of decision distribution."""
    if decisions_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No decisions")
        return fig

    decisions_df = decisions_df.copy()
    decision_counts = decisions_df["final_decision"].value_counts().reset_index()
    decision_counts.columns = ["Decision", "Count"]

    # Map colors
    decision_counts["Color"] = decision_counts["Decision"].map(DECISION_COLORS).fillna(
        "#9ca3af"
    )

    fig = px.bar(
        decision_counts,
        x="Decision",
        y="Count",
        color="Decision",
        color_discrete_map=DECISION_COLORS,
        title="Decision Distribution",
    )

    fig.update_layout(
        height=300,
        xaxis_title="Decision",
        yaxis_title="Count",
        showlegend=False,
    )

    return fig


def build_daily_token_line(daily_stats_df: pd.DataFrame) -> go.Figure:
    """Build line chart of daily token totals."""
    if daily_stats_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No daily stats")
        return fig

    daily_stats_df = daily_stats_df.copy()
    daily_stats_df["date"] = pd.to_datetime(daily_stats_df["date"])
    daily_stats_df = daily_stats_df.sort_values("date")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_stats_df["date"],
            y=daily_stats_df["total_tokens"],
            mode="lines+markers",
            name="Total Tokens",
            line=dict(color="#3b82f6", width=2),
            marker=dict(size=8),
            fill="tozeroy",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Tokens: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Daily Token Usage",
        xaxis_title="Date",
        yaxis_title="Total Tokens",
        height=300,
    )

    return fig
