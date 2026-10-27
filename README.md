# Causal Inference: Fed Rates vs. S&amp;P 500

M2 Causal Inference project — Albert School. Estimating the causal effect of Fed rate decisions on S&amp;P 500 returns.

## Project structure

```
.
├── data/                        # raw & downloaded data (FRED, yfinance)
├── notebooks/
│   └── report_notebook.ipynb    # main analysis notebook
├── results/                     # figures, tables, exported outputs
└── README.md
```

## Data sources


| Series                          | Source                                                                                                                                                                                     | Access                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| Fed funds rate / FOMC decisions | [FRED (Federal Reserve Economic Data)](https://fred.stlouisfed.org/series/FEDFUNDS) or [federalreserve.gov FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) | CSV download or `pandas_datareader` / FRED API |
| S&amp;P 500 prices              | Yahoo Finance                                                                                                                                                                              | `yfinance` Python library (ticker `^GSPC`)     |

## 7-step workflow


| Step              | What to do                                                                                                                              | Notebook output                |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 1. Question       | Name the unit (calendar month), treatment **T** (rate hike/cut/hold), outcome **Y** (S&amp;P 500 return), effect type (ATE/ATT/ATU) | One-sentence causal question   |
| 2. Variables      | Identify confounders (previously available inflation, growth, and market conditions) — never control for post-treatment variables                    | Table of variables + role      |
| 3. Method         | Pick method based on how treatment was assigned (see below)                                                                             | Method + key assumption        |
| 4. Compare groups | Check treated vs. control periods for pre-treatment similarity                                                                          | Descriptive table + plots      |
| 5. Estimate       | Naive difference first, then method-based estimate                                                                                      | Effect + confidence interval   |
| 6. Check          | Robustness checks (alt. controls, placebo dates, subsamples)                                                                            | Short list of checks + results |
| 7. Conclude       | Answer the question, state limits, give a recommendation                                                                                | Conclusion                     |


## Choosing the method (first "yes" wins)

1. **Randomised experiment** — was the rate decision randomly assigned? (No — skip)
2. **Difference-in-Differences** — multiple treated units, data before/after? (e.g., comparing sectors around a rate change)
3. **Synthetic Control** — one treated unit (the market), data before/after a single event?
4. **Observational study** — are main confounders observed in the data?
5. If none fit: refine the question.

The available data are monthly. Begin with descriptive monthly associations. A causal method must address policy endogeneity, anticipation, omitted confounders, and serial dependence. DiD requires credible comparison units and parallel trends; synthetic control requires donors unaffected by the intervention. Other markets may also respond to US monetary policy, so they are not automatically valid controls.

## Monthly data preparation

Run `uv sync`, select the project environment as the notebook kernel, and place the FRED CSV at `data/FEDFUNDS.csv` with columns `observation_date,FEDFUNDS`. Downloaded datasets remain excluded from Git. Record the CSV download date in the notebook.

- One row represents one calendar month. Daily S&P 500 closes are reduced to the last observed close in each completed month; the current month is excluded.
- FEDFUNDS is a monthly average of daily effective rates, in percent ([FRED documentation](https://fred.stlouisfed.org/series/FEDFUNDS)). Its month-start date labels the entire month; it does not imply availability on that date.
- `sp500_return = close[t] / close[t-1] - 1` is a price return, excluding dividends. `rate_change_pp = FEDFUNDS[t] - FEDFUNDS[t-1]` is in percentage points.
- The descriptive exposure is the average-rate change in month t; `next_month_return` is the price return in month t+1. Direction labels describe effective-rate movements, not individual policy decisions or monetary surprises.
- Missing months remain missing. Returns, changes, and leads are computed on a complete calendar index before incomplete analysis rows are removed. No forward fill is used.
- This alignment does not establish causality. Announcement effects require higher-frequency data and a separate identification design. Confounders require publication-aware timing; lagging revised macro data alone does not eliminate look-ahead bias.

## Deliverables

- Written report (~10 pages, PDF) — no code in the report, only figures/tables from the notebook
- Jupyter notebook — runs top to bottom on a fresh environment
- 10-minute presentation

### Report structure

1. Introduction (context, causal question, link to a company decision) — 1p
2. Data (sources, variables, treatment assignment) — 1p
3. Causal framework (potential outcomes, DAG, confounders) — 1.5p
4. Method + key assumption — 1.5p
5. Descriptive analysis (naive diff, group comparison/trends) — 1.5p
6. Results (effect + CI, interpretation) — 2p
7. Checks and limits — 1p
8. Conclusion — 0.5p

## Common mistakes to avoid

- Controlling for variables measured **after** the treatment (e.g., post-announcement volatility)
- Reporting a correlation as a causal effect
- Not specifying whether the estimate is ATE, ATT, or ATU
- Using DiD without checking parallel pre-trends

## Deadline

Report + notebook due **one week before** the oral presentation. No changes accepted after that date.