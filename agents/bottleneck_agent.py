from typing import Any, Dict

from config import MODE, MODEL, OPENAI_API_KEY


def _local_bottleneck_report(analysis: Dict[str, Any]) -> str:
    peak_hours = analysis.get("peak_hours", {})
    slow_hours = analysis.get("slow_hours", {})
    channel_perf = analysis.get("channel_perf", {})
    mismatch = analysis.get("volume_revenue_mismatch", {})

    top_channel = max(channel_perf, key=channel_perf.get) if channel_perf else "unknown"
    weak_channel = min(channel_perf, key=channel_perf.get) if channel_perf else "unknown"

    lines = [
        "=== BOTTLENECKS ===",
        f"- Busy hours to watch: {list(peak_hours.keys())}",
        f"- Quiet hours: {list(slow_hours.keys())}",
        f"- Channel with most revenue right now: {top_channel}",
        f"- Weakest channel by revenue: {weak_channel}",
        f"- Hours that might have lots of orders but weak revenue: {list(mismatch.keys())}",
        "",
        "=== KEY INSIGHTS ===",
        "- Shift a little staffing from quiet hours to busy hours.",
        "- Check prep and handoff times by channel during rush periods.",
        "- Test simple add-ons or bundles in mismatch hours.",
    ]
    return "\n".join(lines)


def _openai_bottleneck_report(analysis: Dict[str, Any]) -> str:
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing. Set MODE=local or provide a key.")

    system_prompt = open("prompts/system_prompt.txt", "r", encoding="utf-8").read()
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(analysis)},
        ],
    )
    return response.choices[0].message.content or "No output generated."


def run_bottleneck_agent(analysis: Dict[str, Any]) -> str:
    if MODE == "openai":
        return _openai_bottleneck_report(analysis)
    return _local_bottleneck_report(analysis)
