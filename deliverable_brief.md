# Deliverable Brief

## Question, in plain terms

When the Fed raises rates at an FOMC meeting, does the S&P 500 move differently than it
would have if the Fed had held instead? We compare meetings where the Fed hiked to
meetings where it held, using only information known the day before each meeting.

## Variables

| Variable                                                                   | Description                           | Role (notebook)                                                  |
| -------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------- |
| `fomc_decision` (hike/hold)                                                | the Fed's decision                    | Treatment                                                        |
| `sp500_close`, `y1`, `y21` (returns after)                                 | S&amp;P 500 return after the decision | Outcome                                                          |
| `fed_target`                                                               | current target rate level             | Confounder (policy path)                                         |
| `target_change_pp`                                                         | size of rate change                   | Not used (subset checks only)                                    |
| `fomc_kind`                                                                | scheduled vs unscheduled meeting      | Not used (subset checks only)                                    |
| `yield_3m`, `yield_1y`, `yield_2y`, `yield_10y`                            | Treasury yields                       | Pre-decision: input to confounders. Post-decision: Mediator      |
| `spread_3m`, `spread_1y`, `spread_2y`                                      | yield minus target                    | Confounder (market expectations)                                 |
| `change_3m_21d`                                                            | 21-day change, 3-month yield          | Confounder (market expectations)                                 |
| `term_spread`                                                              | 10yr minus 3mo yield                  | Confounder (market state)                                        |
| `vix`                                                                      | implied volatility                    | Pre-decision: Confounder (market state). Post-decision: Mediator |
| `credit_spread`                                                            | Baa minus 10yr yield                  | Pre-decision: Confounder (market state). Post-decision: Mediator |
| `inflation_yoy`                                                            | CPI, YoY                              | Confounder (mandate)                                             |
| `unemployment`, `unemp_change_3m`                                          | unemployment rate, 3mo change         | Confounder (mandate)                                             |
| `ind_prod_yoy`                                                             | industrial production, YoY            | Confounder (mandate)                                             |
| `prev_hike`, `prev_cut`                                                    | last decision was hike/cut            | Confounder (policy path)                                         |
| `hikes_12m`, `cuts_12m`                                                    | hikes/cuts in past 12mo               | Confounder (policy path)                                         |
| `sp500_ret_21d`, `sp500_ret_252d`                                          | past S&amp;P return, 21d/252d         | Confounder (market state)                                        |
| `fedfunds_month_avg`                                                       | monthly-avg Fed funds rate            | Not used (audit only)                                            |
| `ftse100`, `dax`, `cac40`, `nikkei225`, `hangseng`, `asx200`, `tsx`, `smi` | foreign index closes                  | Not used (synthetic control donor test only)                     |

Role = Treatment / Outcome / Confounder / Mediator / Not used.

## Method

| Method | Chosen? | Reason |
|---|---|---|
| Randomised experiment | No | The Fed's decision is not randomly assigned |
| Difference-in-Differences | No | No untreated group — a decision hits the whole index at once |
| Synthetic Control | No | Tested against 8 foreign indices; none are untouched by US policy, so no clean donor mix |
| **Observational study** | **Yes** | Main confounders (Fed's mandate: inflation, employment, financial conditions) are observed in the data |

## Estimate

| Method | Reasoning |
|---|---|
| Naive gap | Baseline; biased by selection, reported for comparison only |
| **Regression (headline)** | Guide's recipe; lowest simulated error, but extrapolates past the "contested" hikes where comparable holds exist |
| Standardisation | Predicts Y(0) for hikes from holds; reported for all hikes and contested-only |
| Inverse-odds weighting | Reweights holds to resemble hikes; reported for all hikes and contested-only |

**What would change the decision:** standard-error choice. HC3 (fixed in advance) gives a 21-day
interval of [−6.01, +0.13] (includes zero, no effect claimed). Clustering by year instead gives
[−4.86, −1.02] (excludes zero, effect detected). This single choice is the one place in the
analysis where the headline conclusion flips.

## Compare the groups

| Method/metric | What it answers |
|---|---|
| Propensity score (logit on confounders) | How likely was a hike at this meeting, given what was known before? |
| AUC of that model | How predictable is the decision from observables? |
| Standardized mean difference (SMD), per confounder | How far apart are hike and hold meetings on each variable? |
| Overlap histogram of propensity scores | Do comparable hold meetings exist across the same range as hikes? |
| Effective sample size (Kish ESS) of weighted holds | How many hold meetings is the comparison really resting on? |
| Propensity-band table | In which predictability range do comparable hikes/holds coexist? |
