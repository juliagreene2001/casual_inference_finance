"""Compare the Kaggle S&P 500 close used in notebooks/fed_sp500_daily.csv against
a direct yfinance download, to check whether the Kaggle step can be replaced by the
library call the project already uses for the foreign donor indices.

Run with `uv run python validation/sp500_source_comparison.py`.
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "notebooks" / "fed_sp500_daily.csv"
OUTPUT = ROOT / "validation" / "sp500_source_comparison.csv"


def main() -> None:
    panel = pd.read_csv(PANEL, parse_dates=["date"]).set_index("date")["sp500_close"]

    yfin = yf.download("^GSPC", start=panel.index.min(), end=panel.index.max() + pd.Timedelta(days=1),
                        auto_adjust=False, progress=False)["Close"]
    yfin = yfin.iloc[:, 0] if isinstance(yfin, pd.DataFrame) else yfin
    yfin.name = "yfinance_close"

    both = pd.concat([panel.rename("kaggle_close"), yfin], axis=1)
    missing_in_yfinance = both["kaggle_close"].notna() & both["yfinance_close"].isna()
    missing_in_kaggle = both["yfinance_close"].notna() & both["kaggle_close"].isna()
    compared = both.dropna()
    gap_pct = (compared["kaggle_close"] / compared["yfinance_close"] - 1).abs() * 100

    both.to_csv(OUTPUT)
    print(f"Kaggle rows: {panel.notna().sum()} | yfinance rows: {yfin.notna().sum()}")
    print(f"Compared on {len(compared)} shared dates")
    print(f"Dates in Kaggle but not yfinance: {missing_in_yfinance.sum()}")
    print(f"Dates in yfinance but not Kaggle: {missing_in_kaggle.sum()}")
    print(f"Largest gap: {gap_pct.max():.5f}% | Mean gap: {gap_pct.mean():.5f}%")
    print(f"Dates with gap > 0.01%: {(gap_pct > 0.01).sum()}")
    if (gap_pct > 0.01).any():
        print(compared.loc[gap_pct[gap_pct > 0.01].index].assign(gap_pct=gap_pct[gap_pct > 0.01]))
    print(f"Saved comparison to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
