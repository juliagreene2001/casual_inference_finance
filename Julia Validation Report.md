# Julia Validation Report

A step-by-step validation of the Fed-hike / S&P 500 causal inference project, following the
course guide's seven-step workflow. For each step: what the project does, what was checked,
and what (if anything) should change. Findings with a concrete fix are also written up in
`suggestions.md` for the project's author; this report is the full walkthrough behind them.

No files in `report/`, `notebooks/report_notebook.ipynb`, or `report/analysis_plan.md` were
edited — those are the frozen, submitted record. All validation lives in new files
(`deliverable_brief.md`, `suggestions.md`, this report, and the `validation/` folder).

## Data

**What it does:** merges three sources into `notebooks/fed_sp500_daily.csv` — S&P 500 closes
(Kaggle), FOMC decision dates/classification (Fed's own calendar), and FRED macro/market
series. Every value on a date reflects only what was known by that date's close.

**Checked:**
- Decision counts (52 hikes / 179 holds / 40 cuts) recomputed directly from the CSV,
  independent of `scripts/build_dataset.py` — match exactly.
- Publication-lag rule spot-checked against the real Feb-2022 CPI release (March 10, 2022):
  `inflation_yoy` still shows January's 7.559% on March 18, and correctly jumps to
  February's 7.937% on March 21 — matching the "not known until the 20th of the next month"
  rule and the project's own `test_macro_values_wait_for_publication` test.
- S&P 500 source: compared the Kaggle-sourced close against a direct `yfinance` pull
  (`validation/sp500_source_comparison.py`) — identical to within float rounding
  (max gap 0.00001%) across all 11,111 trading days.

**Finding → suggestion #1:** the Kaggle download step can be dropped in favor of `yfinance`
(already a dependency, already used for the donor indices) with no change to the data —
removes a manual-dataset dependency that was only there to satisfy an earlier (now waived)
Kaggle requirement.

## Question

**What it does:** defines the unit as one FOMC decision (Feb 1994–Oct 2026), treatment as
hike vs. hold, outcome as S&P 500 return at 2-day and 21-day horizons, and the estimand as
the ATT (not ATE) — "in meetings where the Fed hiked, how different would the return have
been under a hold?"

**Checked:** this is a genuinely causal question, not the vaguer "how do rates and stocks
interact" — it isolates one specific decision's effect rather than describing the general
rate/stock relationship. Confirmed the ATT is the right target over ATE: a hike in mid-crisis
was never realistically on the table, so ATE would ask about a world with no real data.

**Finding:** none — well-specified, matches the guide's requirements.

## Variables

**What it does:** sorts every column into treatment / outcome / confounder (by group:
market expectations, policy path, mandate, market state) / mediator / not-used, with an
explicit rule never to adjust for anything measured after the decision.

**Checked:** full variable inventory and the notebook's own sort are both in
`deliverable_brief.md` for side-by-side comparison with an independent read of the same
columns.

**Finding:** none — the confounder/mediator split holds up (e.g. post-decision yields/VIX/
credit spread correctly flagged as mediators, not confounders, when measured after the
decision).

## Method

**What it does:** walks the guide's decision tree in order — not randomized (no RCT); no
untreated group since a decision hits the whole index at once (no DiD); synthetic control
tested against 8 foreign donor indices and rejected (donors aren't clean — they carry the
US decision-day move into their own next session, confirmed via a next-day pass-through
regression); confounders are observed (the Fed's mandate is public) → observational study.

**Checked:** the DiD rejection reasoning was tightened during this review — it's not that
treatment isn't "parallel," it's that there's no comparison group at all (the whole index
moves together). The synthetic-control rejection is backed by an actual regression result,
not just assumed.

**Finding:** none — by elimination as much as by qualification, observational study is the
right call.

## Compare the groups

**What it does:** propensity score (logit on 9 pre-decision controls), AUC (0.97 with market
expectations, 0.86 without), standardized-mean-difference balance table, overlap histogram,
Kish effective sample size (11 with expectations, 28 without), propensity-band table.

**Checked:** all six metrics confirmed present in the notebook (Cells 11–13). One gap vs. the
course: the overlap histogram/band table implements **positivity** (Session 1, slide 36) but
never names it that way — a labeling gap, not a substance gap.

**Finding:** the central fact this step surfaces — 25 of 52 hikes have propensity ≥ 0.9, i.e.
**no comparable hold exists at all** — is the single most consequential number in the whole
project. Everything downstream (why regression extrapolates, why estimators disagree, why
power is low) traces back to this.

## Estimate

**What it does:** four estimators (naive, regression-headline, standardisation, inverse-odds
weighting) at both horizons, 97.5% intervals (Bonferroni for two confirmatory horizons).

**Checked:** confirmed via the notebook's own saved output (Cell 16) that regression
(by Frisch-Waugh-Lovell) is implicitly weighted toward the "contested" hikes but still
extrapolates to predict Y(0) for the 25 hikes with no real counterfactual — making it a
different, less-defensible quantity than the ATT it's presented as. The HC3-vs-clustered-SE
choice is the one place in the whole analysis where switching flips the 21-day conclusion
(HC3: [−6.01, +0.13], includes zero; clustered: [−4.86, −1.02], excludes zero).

**Finding → suggestion #2:** regression's headline status should come with explicit
acknowledgment of the extrapolation, with the contested-only estimates given equal visual
weight. Validated an additional, less arbitrary method — **overlap weighting**
(`validation/overlap_weighting_estimate.py`) — which avoids the 0.9 hard cutoff entirely by
weighting every meeting by `e(X)(1-e(X))`. Result: −0.12 [−0.82, +0.58] at 2 days, −1.33
[−3.12, +0.45] at 21 days — closer to the naive gap than to regression, consistent with the
pattern that the more a method relies on extrapolation, the larger its estimate.

## Check

**What it does:** simulation with a known planted effect, robustness to control sets/subsets/
standard errors, influence check, falsification tests (fake date, lead test, circular shift),
Cinelli-Hazlett sensitivity (robustness value).

**Checked:** the simulation shows the regression's power at 21 days is weak — only ~5% power
to detect a true −1 point effect under the realistic "anticipation" world, against a
literature-plausible true effect of 1–3 points. The robustness value (0.197 at 21 days) means
a hidden confounder would need to be ~3x stronger than the strongest observed control to
null the result out — a concrete, if imperfect, benchmark.

**Finding → suggestion #3:** proposed a follow-up study designed around the power problem,
validated in two parts (both new, standalone — no new data acquired):
- `validation/power_sizing_check.py` extends the power calculation across every horizon
  already in the data (not just 2-day/21-day). Confirms the already-chosen 2-day horizon is
  close to optimally powered for a ~1-point effect (MDE 0.96); 21-day was chosen for business
  relevance, not power, and that tradeoff is explicit and real (MDE 2.55 by this simplified
  calc, 4.2 by the notebook's own regression-based figure — the gap is the overlap problem:
  effective comparable holds are 11–28, not 178).
- A **surprise-based treatment** (Fed funds futures, Kuttner 2001 methodology) was proposed
  as the more fundamental fix to overlap, since it removes the binary positivity problem
  entirely. **Important caveat, added during this review:** this changes the *estimand*, not
  just the method — it estimates a dose-response slope (`dY/d surprise`), not the discrete
  `E[Y(hike)-Y(hold)]` the project currently targets. Adopting it means rewriting the Step 1
  question, not just swapping an estimator. Implementation is blocked on data access (free
  sources don't reliably cover 1994+ futures settlement prices) — explored a buildable
  proxy instead (change in the 3-month Treasury yield around the decision, using data
  already in the project), noting it's noisier than futures but requires no new data source.

## Conclude

**What it does:** applies a four-condition pre-registered rule mechanically to decide whether
a causal effect is "credibly detected," at both horizons.

**Checked:** the rule's mechanical output (Cell 29: FAIL/FAIL/PASS/PASS at 21 days,
FAIL/FAIL/FAIL/PASS at 2 days → no effect credibly detected at either horizon) matches the
numbers reviewed throughout this report, including the new overlap-weighted estimate, which
also doesn't exclude zero at either horizon — an independent method lands on the same
conclusion. The stated recommendation ("don't trade the announcement; treat a lower return
as a stress scenario, not a forecast") is proportionate to evidence this uncertain.

**Finding:** none — the rule is applied correctly, and the conclusion is honestly stated
given the evidence.

## Summary of suggestions for the project author

See `suggestions.md` for the full write-up of each. In brief:

1. Source S&P 500 from `yfinance` instead of Kaggle — validated as a safe, zero-impact swap.
2. Make the regression's extrapolation explicit in the report; give the contested-only /
   overlap-weighted estimates equal billing, not footnote status.
3. If pursuing a follow-up study: size the horizon to the effect (not just relevance), and
   consider a surprise-based treatment to fix overlap at the source — while being clear that
   this reframes the research question rather than patching the current one.

## Validation files

| File | What it does |
|---|---|
| `deliverable_brief.md` | Plain-language question, variable role table, method/estimate reasoning |
| `suggestions.md` | The three suggestions above, in full, for the project author |
| `validation/sp500_source_comparison.py` | Kaggle vs. yfinance S&P 500 comparison |
| `validation/overlap_weighting_estimate.py` | Overlap-weighted (ATO) estimate, both horizons |
| `validation/power_sizing_check.py` | Power/MDE across all available horizons |
