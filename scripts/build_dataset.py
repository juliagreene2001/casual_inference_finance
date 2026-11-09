"""Build the one CSV the notebook reads (notebooks/fed_sp500_daily.csv).

Run this once with `uv run python scripts/build_dataset.py`. It downloads public
data into data/raw/ and merges it. The notebook never downloads anything, so its
results cannot change after this file is frozen.

Time order is the point of this script: every column on a given date holds only
what was known by the close of that date. The one exception is
fedfunds_month_avg, which is used only to audit the old monthly labels.
"""

import re
import ssl
import time
import urllib.request
from pathlib import Path

import certifi
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "notebooks" / "fed_sp500_daily.csv"
START = "1982-10-01"  # first full month of the official target series
USER_AGENT = "causal-project-data-build/1.0"

FRED_SERIES = [
    "DFEDTAR", "DFEDTARU", "DFEDTARL",       # official target (point, then range)
    "DGS3MO", "DGS1", "DGS2", "DGS10",       # Treasury yields, same quoting basis
    "VIXCLS",                                # implied volatility
    "BAA", "GS10",                           # credit spread inputs, monthly
    "CPIAUCSL", "UNRATE", "INDPRO",          # the Fed's mandate, monthly
    "FEDFUNDS",                              # monthly average rate, audit only
]
FOMC_CALENDAR = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FOMC_HISTORICAL = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
DONORS = {
    "ftse100": "^FTSE", "dax": "^GDAXI", "cac40": "^FCHI", "nikkei225": "^N225",
    "hangseng": "^HSI", "asx200": "^AXJO", "tsx": "^GSPTSE", "smi": "^SSMI",
}
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
# Intermeeting moves after 2008 take effect the day after they are announced.
EFFECTIVE_TO_ANNOUNCED = {
    pd.Timestamp("2020-03-04"): pd.Timestamp("2020-03-03"),
    pd.Timestamp("2020-03-16"): pd.Timestamp("2020-03-15"),
}


def download(url: str, path: Path) -> None:
    """Save a URL to disk, skipping files that are already there."""
    if path.exists():
        return
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=90, context=context) as response:
        path.write_bytes(response.read())
    time.sleep(0.2)


def download_raw() -> None:
    (RAW / "fomc").mkdir(parents=True, exist_ok=True)
    for series in FRED_SERIES:
        download(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}", RAW / f"{series}.csv")
    download(FOMC_CALENDAR, RAW / "fomc" / "calendars.htm")
    for year in range(1994, 2021):
        download(FOMC_HISTORICAL.format(year=year), RAW / "fomc" / f"h{year}.htm")

    sp500_path = RAW / "sp500.csv"
    donors_path = RAW / "donors.csv"
    if not sp500_path.exists() or not donors_path.exists():
        import yfinance as yf  # only this script needs it, never the notebook

        if not sp500_path.exists():
            close = yf.download("^GSPC", start="1950-01-01", auto_adjust=False, progress=False)["Close"]
            close = close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
            close.rename("sp500_close").to_csv(sp500_path)

        if not donors_path.exists():
            closes = {}
            for name, ticker in DONORS.items():
                data = yf.download(ticker, start="1990-01-01", auto_adjust=False, progress=False)
                close = data["Close"]
                closes[name] = close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
            pd.DataFrame(closes).to_csv(donors_path)


def fred(series: str) -> pd.Series:
    data = pd.read_csv(RAW / f"{series}.csv", parse_dates=["observation_date"], index_col="observation_date")
    return pd.to_numeric(data[series], errors="coerce")


def month_number(name: str) -> int:
    return MONTHS[name.strip().lower()[:3]]


def parse_fomc_meetings() -> pd.DataFrame:
    """Return scheduled meeting dates, using the last day of each meeting."""
    rows = []
    heading = re.compile(r"<h5[^>]*>\s*([^<]*?)\s*-\s*(\d{4})\s*</h5>")
    days = re.compile(r"^([A-Za-z]+)(?:/([A-Za-z]+))?\s+(\d{1,2})(?:\s*-\s*(?:([A-Za-z]+)\s+)?(\d{1,2}))?$")
    for path in sorted((RAW / "fomc").glob("h*.htm")):
        for match in heading.finditer(path.read_text(encoding="utf-8", errors="replace")):
            text, year = match.group(1).strip(), int(match.group(2))
            lowered = text.lower()
            # Calls and unscheduled sessions count only if the target moved (handled below).
            if "meeting" not in lowered or "cancelled" in lowered or "unscheduled" in lowered:
                continue
            parsed = days.match(re.sub(r"\(.*?\)", "", text).replace("Meeting", "").strip())
            if not parsed:
                raise ValueError(f"Could not read meeting heading: {text} {year}")
            first, slash, day1, second, day2 = parsed.groups()
            month = month_number(second or slash or first)
            rows.append(pd.Timestamp(year, month, int(day2 or day1)))
    calendar_page = (RAW / "fomc" / "calendars.htm").read_text(encoding="utf-8", errors="replace")
    for panel in re.finditer(r"(\d{4}) FOMC Meetings(.*?)(?=\d{4} FOMC Meetings|$)", calendar_page, flags=re.S):
        year = int(panel.group(1))
        meetings = re.finditer(
            r"fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>\s*([^<]+?)\s*<",
            panel.group(2), flags=re.S,
        )
        for meeting in meetings:
            month_name, day_text = meeting.group(1).strip(), meeting.group(2).strip()
            numbers = re.findall(r"\d+", day_text)
            if "notation" in day_text.lower() or not numbers:
                continue
            rows.append(pd.Timestamp(year, month_number(month_name.split("/")[-1]), int(numbers[-1])))
    meetings = pd.DataFrame({"date": sorted(set(rows))})
    # The 2003 page lists September 15 and 16 separately; the decision came on the 16th.
    return meetings[meetings["date"] != pd.Timestamp("2003-09-15")].reset_index(drop=True)


def official_target() -> pd.Series:
    """Target rate in percent: the point target, then the midpoint of the range."""
    midpoint = (fred("DFEDTARU") + fred("DFEDTARL")) / 2
    target = pd.concat([fred("DFEDTAR"), midpoint]).sort_index()
    return target[~target.index.duplicated(keep="last")].asfreq("D").ffill()


def classify_decisions(target: pd.Series, last_date: pd.Timestamp) -> pd.DataFrame:
    """Label each FOMC decision since Feb 1994 as hike, hold or cut."""
    day = pd.Timedelta(days=1)
    scheduled = parse_fomc_meetings()
    scheduled = scheduled[(scheduled["date"] >= "1994-02-01") & (scheduled["date"] <= last_date)].copy()
    scheduled["kind"] = "scheduled"
    # After 2008 the new target takes effect the day after the decision.
    scheduled["change_pp"] = [round(target[d + day] - target[d - day], 4) for d in scheduled["date"]]

    changes = target.diff()
    changes = changes[(changes.abs() > 1e-9) & (changes.index >= "1994-02-01")]
    explained = set(scheduled["date"]) | {d + day for d in scheduled["date"]}
    unscheduled = [
        {"date": EFFECTIVE_TO_ANNOUNCED.get(d, d), "kind": "unscheduled", "change_pp": round(changes[d], 4)}
        for d in changes.index if d not in explained
    ]
    decisions = pd.concat([scheduled, pd.DataFrame(unscheduled)], ignore_index=True).sort_values("date")
    decisions["decision"] = np.select(
        [decisions["change_pp"] > 1e-9, decisions["change_pp"] < -1e-9], ["hike", "cut"], default="hold"
    )
    return decisions.reset_index(drop=True)


def known_macro_month(dates: pd.DatetimeIndex) -> pd.PeriodIndex:
    """Latest month whose data was already published on each date.

    All three series for month M-1 are normally out by the 20th of month M,
    so before the 20th we only trust month M-2.
    """
    months = dates.to_period("M")
    return pd.PeriodIndex([m - 1 if d.day >= 20 else m - 2 for d, m in zip(dates, months)], freq="M")


def as_known(series: pd.Series, months: pd.PeriodIndex) -> np.ndarray:
    """Value for each requested month, carrying forward months never published."""
    monthly = series.dropna().copy()
    monthly.index = monthly.index.to_period("M")
    return monthly.reindex(pd.period_range(monthly.index.min(), months.max(), freq="M")).ffill().reindex(months).to_numpy()


def build_panel() -> pd.DataFrame:
    sp500 = pd.read_csv(RAW / "sp500.csv", index_col=0, parse_dates=True)["sp500_close"].dropna()
    sp500 = sp500[sp500.index >= START].sort_index()
    trading_days = sp500.index

    panel = pd.DataFrame({"sp500_close": sp500.round(2)})
    panel.index.name = "date"

    target = official_target()
    panel["fed_target"] = target.reindex(trading_days).round(4)
    decisions = classify_decisions(target, trading_days.max())
    # A decision announced when markets are closed counts from the next trading day.
    decisions["event_day"] = trading_days[trading_days.searchsorted(decisions["date"], side="left")]
    if decisions["event_day"].duplicated().any():
        raise ValueError("Two decisions fall on one trading day.")
    decisions = decisions.set_index("event_day")
    panel["fomc_decision"] = decisions["decision"].reindex(trading_days)
    panel["fomc_kind"] = decisions["kind"].reindex(trading_days)
    panel["target_change_pp"] = decisions["change_pp"].reindex(trading_days)

    # Daily market series: last value observed on or before each trading day.
    names = {"DGS3MO": "yield_3m", "DGS1": "yield_1y", "DGS2": "yield_2y", "DGS10": "yield_10y", "VIXCLS": "vix"}
    for series, name in names.items():
        panel[name] = fred(series).dropna().reindex(trading_days, method="ffill")

    # Monthly market series: the last completed month is always known.
    credit = fred("BAA") - fred("GS10")
    panel["credit_spread"] = as_known(credit, trading_days.to_period("M") - 1)

    # Macro series: only what had been published by each date.
    months = known_macro_month(trading_days)
    cpi, unemployment, production = fred("CPIAUCSL"), fred("UNRATE"), fred("INDPRO")
    panel["inflation_yoy"] = as_known(cpi.pct_change(12, fill_method=None) * 100, months)
    panel["unemployment"] = as_known(unemployment, months)
    panel["unemp_change_3m"] = as_known(unemployment.diff(3), months)
    panel["ind_prod_yoy"] = as_known(production.pct_change(12, fill_method=None) * 100, months)

    # Audit only: this monthly average includes days after the date on the row.
    monthly_rate = fred("FEDFUNDS")
    monthly_rate.index = monthly_rate.index.to_period("M")
    panel["fedfunds_month_avg"] = monthly_rate.reindex(trading_days.to_period("M")).to_numpy()

    # Foreign indices stay empty on days their markets were closed.
    donors = pd.read_csv(RAW / "donors.csv", parse_dates=[0], index_col=0)
    for name in DONORS:
        panel[name] = donors[name].reindex(trading_days).round(2)

    decimals = {c: 3 for c in ["credit_spread", "inflation_yoy", "unemp_change_3m", "ind_prod_yoy"]}
    return panel.round(decimals).reset_index()


def main() -> None:
    download_raw()
    panel = build_panel()
    OUTPUT.parent.mkdir(exist_ok=True)
    panel.to_csv(OUTPUT, index=False, date_format="%Y-%m-%d")
    counts = panel["fomc_decision"].value_counts().to_dict()
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {panel.shape[0]} rows, {panel.shape[1]} columns")
    print(f"Dates {panel['date'].min().date()} to {panel['date'].max().date()}; decisions {counts}")


if __name__ == "__main__":
    main()
