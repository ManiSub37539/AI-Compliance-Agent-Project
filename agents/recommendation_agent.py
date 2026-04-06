from typing import Any, Dict

from config import MODE, MODEL, OPENAI_API_KEY


def _fmt_hours(hour_map: Dict[int, float]) -> str:
    if not hour_map:
        return "none"
    return ", ".join(str(h) for h in hour_map.keys())


def _fmt_days(day_map: Dict[str, float]) -> str:
    if not day_map:
        return "none"
    return ", ".join(day_map.keys())


def _local_recommendations(analysis: Dict[str, Any], bottleneck_output: str) -> str:
    peak_hours = analysis.get("peak_hours", {})
    slow_hours = analysis.get("slow_hours", {})
    busiest_days = analysis.get("busiest_days", {})
    slow_days = analysis.get("slow_days", {})
    mismatch = analysis.get("volume_revenue_mismatch", {})
    channel_perf = analysis.get("channel_perf", {})
    seasonal_spikes = analysis.get("seasonal_spikes", {})
    seasonal_lulls = analysis.get("seasonal_lulls", {})

    top_channel = max(channel_perf, key=channel_perf.get) if channel_perf else None
    weak_channel = min(channel_perf, key=channel_perf.get) if channel_perf else None

    actions = []

    if peak_hours:
        actions.append(
            f"Staffing: add coverage during peak hours ({_fmt_hours(peak_hours)}), especially on busy days ({_fmt_days(busiest_days)})."
        )

    if slow_hours:
        actions.append(
            f"Schedule smoothing: move breaks, training, and prep into slow hours ({_fmt_hours(slow_hours)})."
        )

    if mismatch:
        actions.append(
            f"Pricing/menu: focus bundles and add-ons in high-volume, low-revenue hours ({_fmt_hours(mismatch)}) to raise ticket size."
        )

    if top_channel and weak_channel and top_channel != weak_channel:
        actions.append(
            f"Channel ops: copy the strongest practices from {top_channel} into {weak_channel} and run a targeted promo for {weak_channel}."
        )

    if seasonal_spikes:
        actions.append(
            f"Seasonality: pre-plan labor and inventory for demand spikes in {_fmt_days(seasonal_spikes)}."
        )

    if seasonal_lulls:
        actions.append(
            f"Seasonality: use {_fmt_days(seasonal_lulls)} for maintenance, training, and retention offers."
        )

    if not actions:
        actions.append("No strong signal found yet. Collect more days of data and rerun.")

    priority = actions[:3]

    lines = [
        "=== RECOMMENDATIONS ===",
        *[f"- {action}" for action in actions],
        "",
        "=== PRIORITY ACTIONS ===",
        *[f"{idx}. {item}" for idx, item in enumerate(priority, start=1)],
        "",
        "=== SIGNALS USED ===",
        f"- Peak hours: {_fmt_hours(peak_hours)}",
        f"- Slow hours: {_fmt_hours(slow_hours)}",
        f"- Busiest days: {_fmt_days(busiest_days)}",
        f"- Slow days: {_fmt_days(slow_days)}",
        f"- Volume/revenue mismatch hours: {_fmt_hours(mismatch)}",
        f"- Strongest channel: {top_channel or 'none'}",
        f"- Weakest channel: {weak_channel or 'none'}",
        f"- Seasonal spikes: {_fmt_days(seasonal_spikes)}",
        f"- Seasonal lulls: {_fmt_days(seasonal_lulls)}",
        "",
        "=== CONTEXT USED ===",
        bottleneck_output[:700],
    ]
    return "\n".join(lines)


def _openai_recommendations(analysis: Dict[str, Any], bottleneck_output: str) -> str:
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing. Set MODE=local or provide a key.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
You are helping a student with a first restaurant analytics project.

Use this analysis:
{analysis}

And this bottleneck draft:
{bottleneck_output}

Return:
- Practical actions for staffing, scheduling, and flow
- Revenue ideas for high-volume low-revenue windows
- A top-3 priority list

Keep the tone straightforward and avoid corporate buzzwords.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or "No output generated."


def refine_recommendations(analysis: Dict[str, Any], bottleneck_output: str) -> str:
    if MODE == "openai":
        return _openai_recommendations(analysis, bottleneck_output)
    return _local_recommendations(analysis, bottleneck_output)
