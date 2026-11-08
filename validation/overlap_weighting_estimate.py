"""Overlap-weighted estimate of the hike/hold effect (Li, Morgan & Zaslavsky, 2018),
as an alternative to the hard 0.9 propensity cutoff used for "contested hikes" in the
main notebook. Rebuilds the same per-meeting table and propensity model as
notebooks/report_notebook.ipynb (cells 3 and 5), then weights each hike by 1 - e(X)
and each hold by e(X) instead of dropping meetings above a cutoff.

The propensity model is refit separately for each horizon, after dropping meetings with
no outcome at that horizon, matching the notebook's own convention (Section 6.6) rather
than fitting one propensity model on the full sample and reusing it at both horizons.

Run with `uv run python validation/overlap_weighting_estimate.py`.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "notebooks" / "fed_sp500_daily.csv"
OUT = ROOT / "validation" / "overlap_weighting_results.csv"

HORIZONS = {"y1": "2-day", "y21": "21-day"}

EXPECTATIONS = ["spread_3m", "spread_1y", "spread_2y", "change_3m_21d"]
POLICY_PATH = ["prev_hike", "prev_cut", "hikes_12m", "cuts_12m", "fed_target"]
MANDATE = ["inflation", "unemployment", "unemp_change_3m", "ind_prod_yoy"]
MARKET_STATE = ["sp500_ret_21d", "sp500_ret_252d", "vix", "credit_spread", "term_spread"]
PROPENSITY = ["spread_3m", "spread_2y", "change_3m_21d", "prev_hike", "inflation", "unemployment",
              "unemp_change_3m", "sp500_ret_21d", "vix"]


def window_return(close, start, end):
    if end >= len(close):
        return np.nan
    return 100 * (close[end] / close[start] - 1)


def build_hike_hold(panel: pd.DataFrame) -> pd.DataFrame:
    close = panel["sp500_close"].to_numpy()
    decision_positions = np.flatnonzero(panel["fomc_decision"].notna().to_numpy())
    decision_dates = panel["date"].to_numpy()[decision_positions]
    decision_labels = panel["fomc_decision"].to_numpy()[decision_positions]

    rows = []
    for position, label in zip(decision_positions, decision_labels):
        opening = position - 1
        day = panel.iloc[opening]
        as_of = np.datetime64(day["date"])
        known = decision_dates <= as_of
        past_year = known & (decision_dates > as_of - np.timedelta64(365, "D"))
        last_decision = decision_labels[known][-1] if known.any() else "hold"
        row = {
            "date": panel["date"].iloc[position],
            "decision": label,
            "spread_3m": day["yield_3m"] - day["fed_target"],
            "spread_1y": day["yield_1y"] - day["fed_target"],
            "spread_2y": day["yield_2y"] - day["fed_target"],
            "change_3m_21d": day["yield_3m"] - panel["yield_3m"].iloc[opening - 21],
            "prev_hike": int(last_decision == "hike"),
            "prev_cut": int(last_decision == "cut"),
            "hikes_12m": int((decision_labels[past_year] == "hike").sum()),
            "cuts_12m": int((decision_labels[past_year] == "cut").sum()),
            "fed_target": day["fed_target"],
            "inflation": day["inflation_yoy"],
            "unemployment": day["unemployment"],
            "unemp_change_3m": day["unemp_change_3m"],
            "ind_prod_yoy": day["ind_prod_yoy"],
            "sp500_ret_21d": window_return(close, opening - 21, opening),
            "sp500_ret_252d": window_return(close, opening - 252, opening),
            "vix": day["vix"],
            "credit_spread": day["credit_spread"],
            "term_spread": day["yield_10y"] - day["yield_3m"],
        }
        for horizon_key in HORIZONS:
            horizon = int(horizon_key[1:])
            row[horizon_key] = window_return(close, opening, opening + 1 + horizon)
        rows.append(row)
    table = pd.DataFrame(rows)
    table["hike"] = (table["decision"] == "hike").astype(int)
    hike_hold = table[table["decision"].isin(["hike", "hold"])].reset_index(drop=True)
    return hike_hold


def main() -> None:
    panel = pd.read_csv(DATA_FILE, parse_dates=["date"])
    hike_hold = build_hike_hold(panel)

    rows = []
    for horizon_key, horizon_label in HORIZONS.items():
        used = hike_hold.dropna(subset=[horizon_key]).copy()
        propensity_model = sm.Logit(used["hike"], sm.add_constant(used[PROPENSITY])).fit(disp=0)
        e = propensity_model.predict(sm.add_constant(used[PROPENSITY]))
        used["overlap_weight"] = np.where(used["hike"] == 1, 1 - e, e)
        fit = smf.wls(f"{horizon_key} ~ hike", data=used, weights=used["overlap_weight"]).fit(cov_type="HC3")
        low, high = fit.conf_int(alpha=0.025).loc["hike"]
        rows.append({"Horizon": horizon_label, "Estimator": "Overlap weighting (ATO)",
                      "Estimate": fit.params["hike"], "Low": low, "High": high, "N": int(len(used))})
        print(f"{horizon_label}: overlap-weighted estimate {fit.params['hike']:+.2f} "
              f"[{low:+.2f}, {high:+.2f}] (n={len(used)})")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Saved to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
