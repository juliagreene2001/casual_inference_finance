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
| 1. Question       | Name the unit (trading day/window), treatment **T** (rate hike/cut/hold), outcome **Y** (S&amp;P 500 return), effect type (ATE/ATT/ATU) | One-sentence causal question   |
| 2. Variables      | Identify confounders (pre-FOMC inflation, GDP growth, prior volatility) — never control for post-treatment variables                    | Table of variables + role      |
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

Given Fed decisions apply market-wide (no untreated control group of "S&amp;P 500s"), **Synthetic Control** (using other indices/assets as controls) or **event-study / DiD across sectors or asset classes** is the likely fit — not a simple observational regression.

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