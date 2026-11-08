"""Which horizon is actually best-powered to detect a plausible effect?

The Check finding in validation/README.md proposes sizing the horizon to the effect, rather than
picking a horizon for substantive relevance and discovering afterward it's underpowered.
This script does that: it computes sigma (hold-group return SD) at every horizon the
notebook already has data for (0, 1, 5, 10, 21, 42, 63 trading days), then reports, at the
STUDY'S ACTUAL SAMPLE SIZE, both the minimum detectable effect at each horizon and the
sample size that would be needed to detect a plausible 1-3 point effect.

This describes the study that already ran (real data, real sample size). It does not
simulate or validate a hypothetical future study (e.g. a Fed-funds-futures surprise design) --
there is no data here to do that with.

Uses the course's planning formula (Session 2, slide 25):
    n_per_arm ~= 2 * sigma^2 * (z_(1-alpha/2) + z_(1-beta))^2 / delta^2
with alpha = 0.025 (Bonferroni for the project's two confirmatory horizons) and power = 80%.
This is a simplification: it treats the comparison as two independent groups, like the
course's worked example, rather than accounting for the 18 regression controls.

Run with `uv run python validation/power_sizing_check.py`.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "notebooks" / "fed_sp500_daily.csv"
OUT = ROOT / "validation" / "power_sizing_results.csv"

ALPHA = 0.025  # two confirmatory horizons, Bonferroni
POWER = 0.80
HORIZONS = [0, 1, 5, 10, 21, 42, 63]  # trading days after the decision; same list the notebook explores
PLAUSIBLE_EFFECTS = [1.0, 2.0, 3.0]  # points; the literature range cited in the oral-defence notes


def window_return(close, start, end):
    if end >= len(close):
        return np.nan
    return 100 * (close[end] / close[start] - 1)


def build_hike_hold(panel: pd.DataFrame) -> pd.DataFrame:
    close = panel["sp500_close"].to_numpy()
    decision_positions = np.flatnonzero(panel["fomc_decision"].notna().to_numpy())
    decision_labels = panel["fomc_decision"].to_numpy()[decision_positions]
    rows = []
    for position, label in zip(decision_positions, decision_labels):
        opening = position - 1
        row = {"date": panel["date"].iloc[position], "decision": label}
        for horizon in HORIZONS:
            row[f"y{horizon}"] = window_return(close, opening, opening + 1 + horizon)
        rows.append(row)
    table = pd.DataFrame(rows)
    return table[table["decision"].isin(["hike", "hold"])].reset_index(drop=True)


def required_n(sigma: float, delta: float) -> float:
    z_alpha = norm.ppf(1 - ALPHA / 2)
    z_power = norm.ppf(POWER)
    return 2 * sigma ** 2 * (z_alpha + z_power) ** 2 / delta ** 2


def minimum_detectable_effect(sigma: float, n: float) -> float:
    z_alpha = norm.ppf(1 - ALPHA / 2)
    z_power = norm.ppf(POWER)
    return (z_alpha + z_power) * sigma * np.sqrt(2 / n)


def main() -> None:
    panel = pd.read_csv(DATA_FILE, parse_dates=["date"])
    hike_hold = build_hike_hold(panel)

    rows = []
    for horizon in HORIZONS:
        key = f"y{horizon}"
        used = hike_hold.dropna(subset=[key])
        holds = used.loc[used["decision"] == "hold", key]
        n_hikes = int((used["decision"] == "hike").sum())
        n_holds = int((used["decision"] == "hold").sum())
        n_per_arm = min(n_hikes, n_holds)
        sigma = float(holds.std())
        mde = minimum_detectable_effect(sigma, n_per_arm)

        row = {"Horizon (days)": horizon, "Hikes": n_hikes, "Holds": n_holds,
               "Hold-group SD": round(sigma, 2), "MDE at current n": round(mde, 2)}
        for delta in PLAUSIBLE_EFFECTS:
            row[f"N needed per arm for {delta:g}pt"] = round(required_n(sigma, delta))
        rows.append(row)

    table = pd.DataFrame(rows)
    table.to_csv(OUT, index=False)

    print(table.to_string(index=False))
    best = table.loc[table["MDE at current n"].idxmin()]
    print(f"\nBest-powered horizon at the actual sample size: {int(best['Horizon (days)'])} days "
          f"(MDE {best['MDE at current n']:.2f} points)")
    print(f"Saved to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
