from typing import Any, Dict
import pandas as pd


def _series_to_int_dict(series: pd.Series) -> Dict[int, float]:
    result: Dict[int, float] = {}
    for key, value in series.items():
        result[int(key)] = round(float(value), 2)
    return result


def _series_to_str_dict(series: pd.Series) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for key, value in series.items():
        result[str(key)] = round(float(value), 2)
    return result


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    # Work on a copy so we do not change the original dataframe from the caller
    data = df.copy()

    # Pull useful time pieces from the timestamp for analysis. This allows us to easily group by these time periods.
    data["hour"] = data["timestamp"].dt.hour
    data["day"] = data["timestamp"].dt.day_name()
    data["month"] = data["timestamp"].dt.month_name()

    # Revenue summaries
    revenue_by_hour = data.groupby("hour")["revenue"].sum()
    revenue_by_day = data.groupby("day")["revenue"].sum()
    revenue_by_month = data.groupby("month")["revenue"].sum()
    revenue_by_channel = data.groupby("channel")["revenue"].sum()

    # Sort highest to lowest for "busiest" views.
    revenue_by_hour_desc = revenue_by_hour.sort_values(ascending=False)
    revenue_by_day_desc = revenue_by_day.sort_values(ascending=False)
    revenue_by_month_desc = revenue_by_month.sort_values(ascending=False)

    # Keep slow windows separate from peak windows when possible.
    peak_hours = revenue_by_hour_desc.head(3)
    slow_hours = revenue_by_hour.sort_values()
    slow_hours = slow_hours[~slow_hours.index.isin(peak_hours.index)].head(3)

    busiest_days = revenue_by_day_desc.head(3)
    slow_days = revenue_by_day.sort_values()
    slow_days = slow_days[~slow_days.index.isin(busiest_days.index)].head(3)

    # Orders vs revenue by hour, used for mismatch detection.
    orders_by_hour = data.groupby("hour")["orders"].sum()
    revenue_by_hour_safe = revenue_by_hour.replace(0, pd.NA)

    # Higher ratio means more orders per dollar, which may suggest low-value baskets.
    orders_per_revenue = (orders_by_hour / revenue_by_hour_safe).dropna()
    mismatch_desc = orders_per_revenue.sort_values(ascending=False)

    seasonal_spikes = revenue_by_month_desc.head(2)
    seasonal_lulls = revenue_by_month.sort_values()
    seasonal_lulls = seasonal_lulls[~seasonal_lulls.index.isin(seasonal_spikes.index)].head(2)

    return {
        "peak_hours": _series_to_int_dict(peak_hours),
        "slow_hours": _series_to_int_dict(slow_hours),
        "busiest_days": _series_to_str_dict(busiest_days),
        "slow_days": _series_to_str_dict(slow_days),
        "seasonality": _series_to_str_dict(revenue_by_month_desc),
        "seasonal_spikes": _series_to_str_dict(seasonal_spikes),
        "seasonal_lulls": _series_to_str_dict(seasonal_lulls),
        "channel_perf": _series_to_str_dict(revenue_by_channel),
        "volume_revenue_mismatch": _series_to_int_dict(mismatch_desc.head(3)),
    }
