from __future__ import annotations

import json
import sys
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
import streamlit as st

from agents.analyzer import analyze
from agents.bottleneck_agent import run_bottleneck_agent
from agents.recommendation_agent import refine_recommendations
from config import MODE, MODEL
from utils.data_loader import load_data
from utils.memory import save_run


# Reuse the integrated compliance/licensing pipeline from the sibling project root.
THIS_FILE = Path(__file__).resolve()
ROOT_REPO = THIS_FILE.parents[2]
LICENSING_MODULE_PATH = ROOT_REPO / "backend" / "app" / "licensing_assistant.py"


def _load_licensing_handler():
    if not LICENSING_MODULE_PATH.exists():
        raise FileNotFoundError(f"Missing licensing module at {LICENSING_MODULE_PATH}")

    licensing_dir = str(LICENSING_MODULE_PATH.parent)
    if licensing_dir not in sys.path:
        sys.path.insert(0, licensing_dir)

    spec = importlib.util.spec_from_file_location("licensing_assistant", LICENSING_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {LICENSING_MODULE_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "handle_licensing_prompt"):
        raise ImportError("licensing_assistant.py does not define handle_licensing_prompt")
    return module.handle_licensing_prompt


handle_licensing_prompt = _load_licensing_handler()


st.set_page_config(page_title="Operations + Compliance Assistant", layout="wide")
st.title("Operations + AI Compliance Assistant")
st.caption("Restaurant analytics workflow plus licensing guardrail and retrieval assistant")

ops_tab, compliance_tab = st.tabs(["Operations Bot", "Compliance + Licensing"])


def _run_operations_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    analysis = analyze(df)
    bottlenecks = run_bottleneck_agent(analysis)
    recommendations = refine_recommendations(analysis, bottlenecks)

    run_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": MODE,
        "model": MODEL,
        "analysis": analysis,
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
    }
    save_run(run_data)
    return run_data


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _pick_first(columns: Dict[str, str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in columns:
            return columns[c]
    return None


def _coerce_uploaded_dataframe(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    # Map original columns to normalized keys for flexible schema matching.
    norm_to_original = {_normalize_name(col): col for col in raw_df.columns}

    timestamp_col = _pick_first(norm_to_original, ["timestamp", "datetime", "date_time"])
    date_col = _pick_first(norm_to_original, ["order_date", "date"])
    time_col = _pick_first(norm_to_original, ["order_time", "time"])

    orders_col = _pick_first(norm_to_original, ["orders", "quantity", "qty"])
    revenue_col = _pick_first(norm_to_original, ["revenue", "total_price", "sales", "amount"])
    channel_col = _pick_first(norm_to_original, ["channel", "pizza_category", "category", "order_channel"])

    if not timestamp_col and not date_col:
        raise ValueError(
            "Could not find timestamp/date columns. Expected one of: "
            "timestamp, datetime, order_date (+ optional order_time)."
        )
    if not orders_col:
        raise ValueError("Could not find orders column. Expected one of: orders, quantity, qty.")
    if not revenue_col:
        raise ValueError("Could not find revenue column. Expected one of: revenue, total_price, sales, amount.")

    df = pd.DataFrame()

    if timestamp_col:
        df["timestamp"] = pd.to_datetime(raw_df[timestamp_col], errors="coerce")
        timestamp_source = timestamp_col
    else:
        if time_col:
            composed = raw_df[date_col].astype(str).str.strip() + " " + raw_df[time_col].astype(str).str.strip()
            df["timestamp"] = pd.to_datetime(composed, errors="coerce")
            timestamp_source = f"{date_col}+{time_col}"
        else:
            df["timestamp"] = pd.to_datetime(raw_df[date_col], errors="coerce")
            timestamp_source = date_col

    df["orders"] = pd.to_numeric(raw_df[orders_col], errors="coerce")
    df["revenue"] = pd.to_numeric(raw_df[revenue_col], errors="coerce")

    if channel_col:
        df["channel"] = raw_df[channel_col].astype(str).fillna("unknown")
        channel_source = channel_col
    else:
        df["channel"] = "in_store"
        channel_source = "default=in_store"

    if df["timestamp"].isna().any():
        bad = int(df["timestamp"].isna().sum())
        raise ValueError(f"{bad} rows have invalid timestamp values after mapping.")

    if df[["orders", "revenue"]].isna().any().any():
        bad_numeric = int(df[["orders", "revenue"]].isna().any(axis=1).sum())
        raise ValueError(f"{bad_numeric} rows have invalid numeric values for orders/revenue after mapping.")

    mapping_note = (
        "Auto-mapped uploaded CSV columns to required schema: "
        f"timestamp<-{timestamp_source}, orders<-{orders_col}, revenue<-{revenue_col}, channel<-{channel_source}."
    )
    return df, mapping_note


with ops_tab:
    st.subheader("Restaurant Data Workflow")
    st.write("Upload a CSV or use your configured DATA_PATH workflow.")

    uploaded = st.file_uploader("Upload restaurant CSV", type=["csv"])

    if st.button("Run Operations Analysis", type="primary"):
        try:
            if uploaded is not None:
                raw_df = pd.read_csv(uploaded)
                df, mapping_note = _coerce_uploaded_dataframe(raw_df)
                st.info(mapping_note)
            else:
                df = load_data("data/sample_data.csv")

            result = _run_operations_pipeline(df)
            st.success("Operations analysis completed.")

            st.markdown("### Analysis")
            st.json(result["analysis"])

            st.markdown("### Bottlenecks")
            st.text(result["bottlenecks"])

            st.markdown("### Recommendations")
            st.text(result["recommendations"])

        except Exception as exc:
            st.error(f"Failed to run operations pipeline: {exc}")


with compliance_tab:
    st.subheader("Compliance + Licensing Query")
    st.write("This runs guardrails first, then retrieval and grounded answer generation if allowed.")

    query = st.text_area(
        "Ask a licensing/compliance question",
        placeholder="Example: How do I create a new OpenGov account for Tiverton business licensing?",
        height=120,
    )
    k = st.slider("Retrieved sources (k)", min_value=1, max_value=8, value=3)

    if st.button("Run Compliance Query", type="primary"):
        if not query.strip():
            st.warning("Please enter a query.")
        else:
            try:
                result = handle_licensing_prompt(query.strip(), k=k)
                decision = result.get("decision", "ALERT")

                if decision == "ALLOW":
                    st.success(f"Decision: {decision}")
                elif decision == "ALERT":
                    st.warning(f"Decision: {decision}")
                else:
                    st.error(f"Decision: {decision}")

                if result.get("answer"):
                    st.markdown("### Answer")
                    st.write(result["answer"])
                elif result.get("user_message"):
                    st.markdown("### Message")
                    st.write(result["user_message"])

                with st.expander("Guardrail Details"):
                    st.json(result.get("guardrail", {}))

                retrieval = result.get("retrieval", [])
                if retrieval:
                    st.markdown("### Retrieved Sources")
                    for idx, chunk in enumerate(retrieval, start=1):
                        score = float(chunk.get("score", 0.0))
                        title = f"#{idx} {chunk.get('file_name')} p.{chunk.get('page_number')} (score={score:.4f})"
                        with st.expander(title):
                            st.write(chunk.get("text", ""))

                with st.expander("Raw Result JSON"):
                    st.code(json.dumps(result, indent=2, ensure_ascii=False), language="json")

            except Exception as exc:
                st.error(f"Compliance flow failed: {exc}")