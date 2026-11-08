# Causal Inference: Fed Rate Hikes and the S&P 500

M2 Causal Inference project, Albert School. An observational study of what an FOMC rate hike does to the S&P 500, compared with a hold.

**Question:** in meetings where the Fed raised its target, how different would the S&P 500 return have been if it had held instead?

**Answer in brief:** no detectable effect in the first two days. Over the following month the evidence leans toward a lower return of roughly one to three points, but it cannot exclude zero, so by the rule fixed in advance no causal effect is claimed. See the report for the details.

## Deliverables

| File | What it is |
|---|---|
| [report/fed_sp500_report.pdf](report/fed_sp500_report.pdf) | The report, about 10 pages, no code |
| [notebooks/report_notebook.ipynb](notebooks/report_notebook.ipynb) | The notebook, which runs from top to bottom on one file |
| [notebooks/fed_sp500_daily.csv](notebooks/fed_sp500_daily.csv) | That one file; it must sit next to the notebook |

## Run it

```bash
uv sync
uv run jupyter nbconvert --to notebook --execute notebooks/report_notebook.ipynb --inplace
uv run python report/build_report.py
```

Or open the notebook in any Jupyter environment and use **Restart and Run All**. It needs only the libraries in `requirements.txt`, downloads nothing, and takes about a minute. It writes figures, tables and every quoted number to `results/`, and `report/build_report.py` reads them from there. Building the report needs the fonts of macOS.

## Project structure

```
.
├── notebooks/
│   ├── report_notebook.ipynb    # main analysis: the guide's seven steps, then two further questions
│   └── fed_sp500_daily.csv      # the one data file
├── report/
│   ├── fed_sp500_report.pdf     # the report
│   ├── build_report.py          # builds the PDF from results/
│   ├── analysis_plan.md         # plan frozen before the final run
│   └── oral_defence_notes.md    # preparation for the oral
├── scripts/
│   ├── build_dataset.py         # downloads public data and builds the CSV
│   └── audit_dataset.py         # checks the CSV against independent sources
├── tests/test_dataset.py        # checks on the CSV
├── results/                     # generated figures and tables, not in git
└── src/                         # earlier monthly code, no longer used
```

## Data

`scripts/build_dataset.py` merges these once. The notebook never downloads anything.

| Content | Source |
|---|---|
| S&P 500 daily closes | [Kaggle: S&P 500 (^GSPC) Historical Data](https://www.kaggle.com/datasets/paveljurke/s-and-p-500-gspc-historical-data) |
| FOMC meeting dates | [Federal Reserve calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) |
| Official target, yields, VIX, credit spread, CPI, unemployment, industrial production | [FRED](https://fred.stlouisfed.org) |
| Foreign indices, used only to assess synthetic control | Yahoo Finance |

Every value on a date is what was known by that close. All 92 target changes since 1994 match the Fed's [own list](https://www.federalreserve.gov/monetarypolicy/openmarket.htm).

## Design

| Step | Choice |
|---|---|
| Unit | One FOMC decision, February 1994 to October 2026 |
| Treatment | Hike vs hold (52 vs 179); the 40 cuts are exploratory |
| Outcomes | S&P 500 price return from the close before the decision to 1 and to 21 trading days after it |
| Effect | ATT, for all hikes and for contested hikes, where comparable holds exist |
| Method | Observational study: regression, standardisation, inverse-odds weighting |
| Key assumption | Conditional exchangeability, given market expectations, the policy path, the Fed's mandate and the market state |
| Checks | Simulation with a known effect, other controls and subsets, influence, fake dates, lead test, circular shifts, sensitivity to a hidden confounder |

## Deadline

Report and notebook are due **one week before** the oral presentation. No changes are accepted after that date.
