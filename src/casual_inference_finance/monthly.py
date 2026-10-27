"""Calendar-month alignment for descriptive Fed rate / equity analysis."""

import pandas as pd


def prepare_monthly_data(prices: pd.Series, fed: pd.DataFrame) -> pd.DataFrame:
    """Align closing prices and FEDFUNDS without filling missing observations.

    Prices may be daily or monthly. Returns are fractions, and rate changes
    are percentage points. The outcome is the following month's price return.
    This timing convention does not establish causal identification.
    """
    if prices.empty or fed.empty:
        raise ValueError("Both price and Fed datasets must contain observations.")
    prices = prices.copy()
    prices.index = pd.to_datetime(prices.index)
    if prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)
    prices = pd.to_numeric(prices, errors="raise").sort_index()
    month_end = prices.groupby(prices.index.to_period("M")).last()

    rates = fed.copy()
    rates.index = pd.to_datetime(rates["observation_date"]).dt.to_period("M")
    if rates.index.has_duplicates:
        raise ValueError("FEDFUNDS must have at most one observation per month.")
    rates = pd.to_numeric(rates["FEDFUNDS"].replace(".", float("nan")), errors="raise")
    # Reindex before differencing: gaps must not become multi-month returns.
    start = min(month_end.index.min(), rates.index.min())
    end = max(month_end.index.max(), rates.index.max())
    months = pd.period_range(start, end, freq="M", name="month")
    result = pd.DataFrame({"sp500_close": month_end, "fed_rate": rates}, index=months)
    result["sp500_return"] = result["sp500_close"].pct_change(fill_method=None)
    result["rate_change_pp"] = result["fed_rate"].diff()
    result["next_month_return"] = result["sp500_return"].shift(-1)
    # Direction refers to the monthly average effective rate, not FOMC decisions.
    change = result["rate_change_pp"].round(8)
    result["rate_direction"] = pd.Series(pd.NA, index=months, dtype="string")
    for mask, label in [(change > 0, "increase"), (change < 0, "decrease"), (change == 0, "unchanged")]:
        result.loc[mask, "rate_direction"] = label
    return result.loc[month_end.index.min():month_end.index.max()]
