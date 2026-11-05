"""Check notebooks/fed_sp500_daily.csv against sources not used to build it.

Run with `uv run python scripts/audit_dataset.py`. It compares the decision labels
with the Fed's own list of target changes and a second Kaggle dataset, and the
S&P 500 closes with Yahoo Finance. The notebook does not need this script.
"""

import io
import re
import ssl
import urllib.request
import zipfile
from pathlib import Path

import certifi
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
OPEN_MARKET_PAGES = [
    "https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
    "https://www.federalreserve.gov/monetarypolicy/openmarket_archive.htm",
]
KAGGLE_FED = "https://www.kaggle.com/api/v1/datasets/download/federalreserve/interest-rates"
ONE_DAY = pd.Timedelta(days=1)


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "causal-project-data-audit/1.0"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=90, context=context) as response:
        return response.read()


def official_changes():
    """Parse the Fed's table of target changes: date, increase, decrease (basis points)."""
    # The date cell can hold a footnote link, as in "March 4*".
    row = re.compile(r"<tr[^>]*>\s*<t[dh][^>]*>\s*([A-Za-z]+\.?\s+\d{1,2})(?:(?!</t[dh]>).)*</t[dh]>\s*<td[^>]*>\s*([^<]*?)\s*</td>\s*<td[^>]*>\s*([^<]*?)\s*</td>", re.S)
    rows = []
    for url in OPEN_MARKET_PAGES:
        html = fetch(url).decode("utf-8", errors="replace")
        for section in re.finditer(r"<h4>(\d{4})</h4>(.*?)</table>", html, flags=re.S):
            for day, increase, decrease in row.findall(section.group(2)):
                rising = bool(re.fullmatch(r"\d+(\.\d+)?", increase)) and float(increase) > 0
                rows.append({"date": pd.Timestamp(f"{day.replace('.', '')} {section.group(1)}"), "direction": "hike" if rising else "cut"})
    changes = pd.DataFrame(rows).drop_duplicates("date").sort_values("date")
    return changes[changes["date"] >= "1994-01-01"].reset_index(drop=True)


def main():
    panel = pd.read_csv(ROOT / "notebooks" / "fed_sp500_daily.csv", parse_dates=["date"])
    decisions = panel.dropna(subset=["fomc_decision"])
    moves = decisions[decisions["fomc_decision"].isin(["hike", "cut"])]

    official = official_changes()
    unmatched = []
    for _, change in official.iterrows():
        # The official date is the effective date, up to a day after the decision (a weekend for March 2020).
        near = moves[(moves["date"] >= change["date"] - ONE_DAY) & (moves["date"] <= change["date"] + ONE_DAY)]
        if len(near) != 1 or near["fomc_decision"].iloc[0] != change["direction"]:
            unmatched.append(str(change["date"].date()))
    extra = [str(d.date()) for d in moves["date"] if not ((official["date"] >= d - ONE_DAY) & (official["date"] <= d + 2 * ONE_DAY)).any()]
    print(f"Fed's own list: {len(official)} changes; decisions in the file: {len(moves)}; not matched: {unmatched}; in the file only: {extra}")

    with zipfile.ZipFile(io.BytesIO(fetch(KAGGLE_FED))) as archive:
        kaggle = pd.read_csv(archive.open("index.csv"))
    kaggle.index = pd.to_datetime(dict(year=kaggle["Year"], month=kaggle["Month"], day=kaggle["Day"]))
    target = pd.concat([kaggle["Federal Funds Target Rate"].dropna(), kaggle["Federal Funds Upper Target"].dropna()]).sort_index()
    change = target[~target.index.duplicated(keep="last")].diff()
    change = change[(change.abs() > 1e-9) & (change.index >= "1994-01-01") & (change.index <= "2017-03-31")]
    in_period = moves[moves["date"] <= "2017-03-31"]
    missing = [str(d.date()) for d in change.index if not ((in_period["date"] >= d - ONE_DAY) & (in_period["date"] <= d + ONE_DAY)).any()]
    print(f"Second Kaggle dataset, 1994 to March 2017: {len(change)} changes; decisions in the file: {len(in_period)}; not matched: {missing}")

    closes = yf.download("^GSPC", start="1982-01-01", auto_adjust=False, progress=False)["Close"]
    closes = closes.iloc[:, 0] if isinstance(closes, pd.DataFrame) else closes
    both = pd.concat([panel.set_index("date")["sp500_close"], closes.rename("yahoo")], axis=1, sort=True).dropna()
    print(f"S&P 500 vs Yahoo Finance: {len(both)} days; largest gap {((both['sp500_close'] / both['yahoo'] - 1).abs().max()) * 100:.5f}%")


if __name__ == "__main__":
    main()
