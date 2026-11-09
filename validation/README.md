# Validation

Checks on the data, variables, method, comparability, estimates and conclusion behind the
analysis in `notebooks/report_notebook.ipynb` and `report/fed_sp500_report.pdf`, following the
course guide's seven-step workflow plus the data build. Scripts behind each check, and their
output, are in this folder.

## Data

**What it does:** merges three sources into `notebooks/fed_sp500_daily.csv` — S&P 500 closes
(Yahoo Finance, via `yfinance`), FOMC decision dates/classification (Fed's own calendar), and
FRED macro/market series. Every value on a date reflects only what was known by that date's
close.

**Checked:**
- Decision counts (52 hikes / 179 holds / 40 cuts) recomputed directly from the CSV,
  independent of `scripts/build_dataset.py` — match exactly.
- Publication-lag rule spot-checked against the real Feb-2022 CPI release (March 10, 2022):
  `inflation_yoy` still shows January's 7.559% on March 18, and correctly jumps to
  February's 7.937% on March 21 — matching the "not known until the 20th of the next month"
  rule and the project's own `test_macro_values_wait_for_publication` test.
- S&P 500 closes cross-checked against a fresh pull of the same source
  (`sp500_source_comparison.py`) — match to within float rounding (max gap 0.00001%) across
  all 11,111 trading days.

**Finding:** none — the build is reproducible and matches independent checks.

## Question

**What it does:** defines the unit as one FOMC decision (Feb 1994–Oct 2026), treatment as
hike vs. hold, outcome as S&P 500 return at 2-day and 21-day horizons, and the estimand as
the ATT (not ATE) — "in meetings where the Fed hiked, how different would the return have
been under a hold?"

**Checked:** this is a genuinely causal question, not the vaguer "how do rates and stocks
interact" — it isolates one specific decision's effect rather than describing the general
rate/stock relationship. The ATT is the right target over ATE: a hike in mid-crisis was never
realistically on the table, so ATE would ask about a world with no real data.

**Finding:** none — well-specified, matches the guide's requirements.

## Variables

**What it does:** sorts every column into treatment / outcome / confounder (by group: market
expectations, policy path, mandate, market state) / mediator / not-used, with an explicit
rule never to adjust for anything measured after the decision.

| Variable                                                                   | Description                           | Role (notebook)                                                  |
| --------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------ |
| `fomc_decision` (hike/hold)                                                | the Fed's decision                    | Treatment                                                        |
| `sp500_close`, `y1`, `y21` (returns after)                                 | S&amp;P 500 return after the decision | Outcome                                                          |
| `fed_target`                                                               | current target rate level             | Confounder (policy path)                                         |
| `target_change_pp`                                                        | size of rate change                   | Not used (subset checks only)                                    |
| `fomc_kind`                                                                | scheduled vs unscheduled meeting      | Not used (subset checks only)                                    |
| `yield_3m`, `yield_1y`, `yield_2y`, `yield_10y`                            | Treasury yields                       | Pre-decision: input to confounders. Post-decision: Mediator      |
| `spread_3m`, `spread_1y`, `spread_2y`                                      | yield minus target                    | Confounder (market expectations)                                 |
| `change_3m_21d`                                                            | 21-day change, 3-month yield          | Confounder (market expectations)                                 |
| `term_spread`                                                              | 10yr minus 3mo yield                  | Confounder (market state)                                        |
| `vix`                                                                      | implied volatility                    | Pre-decision: Confounder (market state). Post-decision: Mediator |
| `credit_spread`                                                           | Baa minus 10yr yield                  | Pre-decision: Confounder (market state). Post-decision: Mediator |
| `inflation_yoy`                                                           | CPI, YoY                              | Confounder (mandate)                                             |
| `unemployment`, `unemp_change_3m`                                         | unemployment rate, 3mo change         | Confounder (mandate)                                             |
| `ind_prod_yoy`                                                            | industrial production, YoY            | Confounder (mandate)                                             |
| `prev_hike`, `prev_cut`                                                   | last decision was hike/cut            | Confounder (policy path)                                         |
| `hikes_12m`, `cuts_12m`                                                   | hikes/cuts in past 12mo               | Confounder (policy path)                                         |
| `sp500_ret_21d`, `sp500_ret_252d`                                         | past S&amp;P return, 21d/252d         | Confounder (market state)                                        |
| `fedfunds_month_avg`                                                      | monthly-avg Fed funds rate            | Not used (audit only)                                            |
| `ftse100`, `dax`, `cac40`, `nikkei225`, `hangseng`, `asx200`, `tsx`, `smi` | foreign index closes                  | Not used (synthetic control donor test only)                     |

**Checked:** this independent column-by-column sort matches the notebook's own.

**Finding:** none — the confounder/mediator split holds up (e.g. post-decision yields/VIX/
credit spread correctly flagged as mediators, not confounders, when measured after the
decision).

## Method

**What it does:** walks the guide's decision tree in order:

| Method | Chosen? | Reason |
|---|---|---|
| Randomised experiment | No | The Fed's decision is not randomly assigned |
| Difference-in-Differences | No | No untreated group — a decision hits the whole index at once |
| Synthetic Control | No | Tested against 8 foreign indices; none are untouched by US policy, so no clean donor mix |
| **Observational study** | **Yes** | Main confounders (Fed's mandate: inflation, employment, financial conditions) are observed in the data |

**Checked:** the DiD rejection holds up — it's not that treatment isn't "parallel," it's that
there's no comparison group at all (the whole index moves together). The synthetic-control
rejection is backed by an actual regression result (a next-day pass-through test on the 8
donor indices), not just asserted.

**Finding:** none — by elimination as much as by qualification, observational study is the
right call.

## Compare the groups

**What it does:**

| Method/metric | What it answers |
|---|---|
| Propensity score (logit on confounders) | How likely was a hike at this meeting, given what was known before? |
| AUC of that model | How predictable is the decision from observables? |
| Standardized mean difference (SMD), per confounder | How far apart are hike and hold meetings on each variable? |
| Overlap histogram of propensity scores | Do comparable hold meetings exist across the same range as hikes? |
| Effective sample size (Kish ESS) of weighted holds | How many hold meetings is the comparison really resting on? |
| Propensity-band table | In which predictability range do comparable hikes/holds coexist? |

AUC is 0.97 with market expectations, 0.86 without; Kish ESS is 11 with expectations, 28
without.

**Checked:** all six metrics are present in the notebook (Cells 11–13). One gap: the overlap
histogram/band table implements **positivity** (Session 1, slide 36) without naming it that —
a labeling gap, not a substance gap.

**Finding:** the central fact this step surfaces — 25 of 52 hikes have propensity ≥ 0.9, i.e.
**no comparable hold exists at all** — is the single most consequential number in the whole
project. Everything downstream (why regression extrapolates, why estimators disagree, why
power is low) traces back to this.

## Estimate

**What it does:**

| Method | Reasoning |
|---|---|
| Naive gap | Baseline; biased by selection, reported for comparison only |
| **Regression (headline)** | Guide's recipe; lowest simulated error, but extrapolates past the "contested" hikes where comparable holds exist |
| Standardisation | Predicts Y(0) for hikes from holds; reported for all hikes and contested-only |
| Inverse-odds weighting | Reweights holds to resemble hikes; reported for all hikes and contested-only |
| Overlap weighting | Weights each hike by `1 - e(X)` and each hold by `e(X)`; targets meetings where both decisions were plausible (notebook Section 6.6) |

Estimators run at both horizons, 97.5% intervals (Bonferroni for two confirmatory horizons).

**What would change the decision:** standard-error choice. HC3 (fixed in advance) gives a
21-day interval of [−6.01, +0.13] (includes zero, no effect claimed). Clustering by year
instead gives [−4.86, −1.02] (excludes zero, effect detected). This is the one place in the
whole analysis where switching flips the 21-day conclusion.

**Checked:** regression (by Frisch-Waugh-Lovell) is implicitly weighted toward the
"contested" hikes but still extrapolates to predict Y(0) for the 25 hikes with no real
counterfactual — a different, less-defensible quantity than the ATT it's presented as.
Overlap weighting avoids the 0.9 hard cutoff entirely and gives a result closer to the naive
gap than to regression, consistent with the pattern that the more a method relies on
extrapolation, the larger its estimate:

| Horizon | Regression (all hikes, extrapolated) | Standardisation, contested | Overlap weighting |
|----|---|---|---|
| 2-day   | −0.31 [−1.11, +0.49] | −0.38 [−1.10, +0.64] | −0.21 [−1.01, +0.60] |
| 21-day  | **−2.94** [−6.01, +0.13] | −2.44 [−5.75, +0.23] | −1.47 [−3.72, +0.77] |

**Finding:** regression's headline status should come with explicit acknowledgment of the
extrapolation it rests on — the report gives the contested-only and overlap-weighted
estimates equal visual weight for this reason.

The overlap-weighted point estimate above matches the notebook's own Section 6.6 exactly
(−1.47 at 21 days): `overlap_weighting_estimate.py` refits the propensity model separately
for each horizon, after dropping meetings with no outcome at that horizon (the 21-day fit
excludes the one hold with no 21-day window yet), the same convention the notebook uses. The
interval differs slightly (analytic HC3 here, −3.72 to +0.77, versus the notebook's year-block
bootstrap, −3.82 to +0.19) — that's a separate choice of interval method, not the propensity
model, and isn't harmonized here.

## Check

**What it does:** simulation with a known planted effect, robustness to control sets/subsets/
standard errors, influence check, falsification tests (fake date, lead test, circular shift),
Cinelli-Hazlett sensitivity (robustness value), and power/minimum-detectable-effect (notebook
Section 8.2).

**Checked:** the simulation shows the regression's power at 21 days is weak — only ~5% power
to detect a true −1 point effect under the realistic "anticipation" world, against a
literature-plausible true effect of 1–3 points. Using the regression's own standard error
(controls plus robust SEs), the minimum detectable effect at 21 days is 4.23 points; reliably
detecting a 2-point effect would take about 232 hikes, roughly 146 years of decisions at the
pace since 1994. The robustness value (0.197 at 21 days) means a hidden confounder would need
to be ~3x stronger than the strongest observed control to null the result out.

**Finding — the project's main open limitation:** waiting for more data is not a realistic
fix at this pace. Two gaps would need to be closed in a future, pre-registered study rather
than a re-analysis of this one:
- **Power.** A follow-up should size its horizon and sample to a target effect from the
  outset, rather than choosing a horizon for business relevance and discovering afterward
  that it cannot detect a plausible effect. `power_sizing_check.py` gives the formula and
  the trade-off across horizons, using a simplified two-group calculation: at 21 days it
  gives an MDE of 2.55 points, lower than the notebook's own 4.23. The notebook's figure is
  the authoritative one — it uses the regression's own standard error, which already reflects
  the 18 controls and the robust SEs, where the simplified calculation does not. The gap is
  the overlap problem from the Compare-the-groups step: the effective number of comparable
  holds (Kish ESS) is only 11–28, not 178, and the two-group formula doesn't capture that
  shrinkage.
- **Overlap.** Both hikes and cuts are highly predictable from public information (AUC 0.86
  and 0.988), so the binary hike/hold/cut treatment barely varies in the region that matters —
  half of all hikes, and most cuts, are already near-certain the day before. A **surprise-based
  treatment** (the market-implied surprise around the announcement, e.g. from Fed funds
  futures, Kuttner 2001) targets this directly: it uses the variation that a binary label
  throws away, and would let cuts be analyzed too — they currently cannot be (27 of 40 cuts
  have almost no comparable hold). This changes the *estimand*, not just the method: it
  estimates a dose-response slope (`dY/d surprise`), not the discrete `E[Y(hike)-Y(hold)]`
  this project targets, so it means rewriting the Question step, not swapping an estimator.
  A separate refinement, if adopted: decomposing the surprise into a pure policy move versus
  a "Fed information" component (Jarociński & Karadi, 2020; Nakamura & Steinsson, 2018,
  both already in the report's references) would avoid attributing a surprise that is really
  the Fed signalling bad news about the economy to the policy action itself.

A further option, independent of data access: since the Fed's meeting schedule is public and
set years in advance, a follow-up could pre-register predictions for a fixed number of future
meetings and score them prospectively as they occur, rather than relying only on a backward-
looking historical sample.

## Conclude

**What it does:** applies a four-condition pre-registered rule mechanically to decide whether
a causal effect is "credibly detected," at both horizons.

**Checked:** the rule's mechanical output (Cell 29: FAIL/FAIL/PASS/PASS at 21 days,
FAIL/FAIL/FAIL/PASS at 2 days → no effect credibly detected at either horizon) matches the
numbers reviewed throughout this walkthrough, including the overlap-weighted estimate above,
which also doesn't exclude zero at either horizon — an independent method lands on the same
conclusion. The stated recommendation ("don't trade the announcement; treat a lower return as
a stress scenario, not a forecast") is proportionate to evidence this uncertain.

**Finding:** none — the rule is applied correctly, and the conclusion is honestly stated
given the evidence.

## Files in this folder

| File | What it does |
|---|---|
| `sp500_source_comparison.py` / `.csv` | Cross-checks S&P 500 closes against a fresh pull of the source |
| `overlap_weighting_estimate.py` / `.csv` | Overlap-weighted (ATO) estimate, both horizons |
| `power_sizing_check.py` / `.csv` | Power/minimum-detectable-effect across all available horizons |
