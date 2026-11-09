# Analysis plan, frozen before final estimation

This file is committed before the final notebook is run, so git shows that these choices were fixed first.

**Disclosure.** An earlier test run looked at several outcome windows and estimators, so this plan is not blind to the data. The propensity model below was chosen using treatment and pre-decision data only, with no post-decision return in the script.

## Question and sample

- **Question:** in meetings where the Fed raised its target, how different would the S&P 500 return have been if it had held instead?
- **Unit:** one FOMC decision, February 1994 to October 2026.
- **Treatment:** hike = 1, hold = 0. Cuts are analysed separately and are exploratory.
- **Estimand:** ATT, for all 52 hikes and for "contested" hikes (propensity below 0.9), the group where comparable holds exist.

## Outcomes (two confirmatory horizons)

S&P 500 price return, in percent, from the close before the decision to:

1. the close one trading day after the decision ("2-day"), the sharp test;
2. the close 21 trading days after the decision ("21-day"), the business horizon.

Each horizon is tested at 2.5% (Bonferroni for two tests), so main-table intervals are 97.5%. Every other horizon is exploratory.

## Controls, all measured before the outcome window opens

- **Market expectations:** 3-month, 1-year and 2-year yields minus the target; 21-day change in the 3-month yield.
- **Policy path:** last decision was a hike; last decision was a cut; hikes and cuts in the past 12 months; target level.
- **Fed's mandate, last published:** inflation, unemployment, 3-month change in unemployment, industrial production growth.
- **Market state:** S&P return over the past 21 and 252 trading days, VIX, credit spread, 10-year minus 3-month yield.

## Estimators

| Label | Estimator | Population | Interval |
|---|---|---|---|
| Naive | Hike mean minus hold mean | All | HC3 |
| **Regression (headline)** | OLS on hike and all 18 controls, the guide's method | Leans toward contested meetings | HC3 |
| Standardisation | Outcome model on holds, predicted for hikes (Session 1) | All hikes; contested hikes | Year-block bootstrap |
| Inverse-odds weighting | Holds weighted by e/(1-e) (Session 1) | All hikes; contested hikes | Year-block bootstrap |

**Propensity model:** logit on the 3-month spread, 2-year spread, 21-day change in the 3-month yield, last decision was a hike, inflation, unemployment, 3-month change in unemployment, past 21-day S&P return, VIX.

## Rule for claiming a causal effect

An effect counts as credibly detected at a horizon only if all four conditions hold:

1. The regression 97.5% interval excludes zero.
2. Both contested-hike estimators have the regression's sign, and at least one 97.5% interval excludes zero.
3. The fake-date placebo (same window placed just before the decision, controls measured before it) has a 97.5% interval that includes zero, and its size is under half the regression estimate.
4. The lead test (next meeting's hike added to the regression) is not significant at 2.5%, and its size is under half the regression estimate.

Otherwise the result is reported as an association, and no causal effect is claimed.

## Checks (reported whatever they show)

- Other control sets, and dropping each control in turn
- Subsets: no near-zero-rate meetings, 1994 to 2007, 2008 to 2026, without crisis years, 25 bp hikes only, scheduled meetings only, windows ending before the next decision
- Leave one hiking cycle out; compare within the same calendar year
- Other standard errors: clustered by year, Newey-West
- Log returns instead of simple returns
- Fake dates, post-minus-pre comparison, lead test, circular shift of the hike sequence
- Sensitivity to a hidden confounder: robustness value, with observed controls as benchmarks
- Simulation with a known effect, to see which estimators recover it under this overlap

## Exploratory only

Cuts versus holds, hike size, other horizons, and effects by how expected the hike was.

## Corrections from the test run

- Yields now share one quoting basis (3-month constant maturity, not the T-bill discount rate).
- After 2008 the target is the midpoint of the range, not the upper limit.
- The 3-month spread and its 21-day change are now among the regression controls.
- Placebo windows have the same length as the outcome window, and their controls are measured before they open.
- Every main-table interval uses the same 97.5% level.

## Addendum, written after the final run

The sections above are unchanged since the freeze; git history shows the original commit. These items were added afterwards and are labelled in the notebook and the report. None of them changes the headline estimate or the rule.

- **Influence checks:** added because dropping a few windows moved the 21-day result more than expected.
- **Within-band estimator:** added as a simple, transparent comparison of hikes and holds with similar propensity.
- **Synthetic control evidence:** the pass-through test uses scheduled meetings only, because intermeeting moves are announced at irregular hours.
- **Overlap weighting:** added after our internal review as a check on the 0.9 cut-off that defines contested hikes. It targets meetings where both decisions were plausible, not the ATT, and it is not part of the rule. Notebook Section 6.6.
- **Further questions:** whether rate cuts lift stocks, and how many hikes it would take to detect an effect of a given size. Added at the end of the project as exploration, not evidence. Notebook Section 8; the report quotes one sentence from each.
- **S&P 500 source:** `scripts/build_dataset.py` now pulls closes from `yfinance` instead of Kaggle, following `validation/sp500_source_comparison.py`'s check that the two sources agree to within float rounding. `notebooks/fed_sp500_daily.csv` itself was not rebuilt, so it keeps its original Kaggle provenance; the switch applies to any future rebuild, not to the frozen file this analysis used.
