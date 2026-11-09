# Causal Inference: Fed Rate Hikes and the S&amp;P 500

M2 Causal Inference project, Albert School. An observational study of what an FOMC rate hike does to the S&amp;P 500, compared with a hold.

**Question:** in meetings where the Fed raised its target, how different would the S&amp;P 500 return have been if it had held instead?

**Answer in brief:** no detectable effect in the first two days. Over the following month the evidence leans toward a lower return of roughly one to three points, but it cannot exclude zero, so by the rule fixed in advance no causal effect is claimed. See the report for the details.

## Deliverables


| File                                                                | What it is                                              |
| ------------------------------------------------------------------- | ------------------------------------------------------- |
| [report/fed\_sp500\_report.pdf](report/fed_sp500_report.pdf)        | The report, about 10 pages, no code                     |
| [notebooks/report\_notebook.ipynb](notebooks/report_notebook.ipynb) | The notebook, which runs from top to bottom on one file |
| [notebooks/fed\_sp500\_daily.csv](notebooks/fed_sp500_daily.csv)    | That one file; it must sit next to the notebook         |


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
│   └── analysis_plan.md         # plan frozen before the final run
├── scripts/
│   ├── build_dataset.py         # downloads public data and builds the CSV
│   └── audit_dataset.py         # checks the CSV against independent sources
├── tests/test_dataset.py        # checks on the CSV
├── validation/                  # checks on the data, design and estimates above
│   └── README.md                # step-by-step checks, with evidence
└── results/                     # generated figures and tables, not in git
```

## Data

`scripts/build_dataset.py` merges these once. The notebook never downloads anything.


| Content                                                                               | Source                                                                                       |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| S&amp;P 500 daily closes                                                              | Yahoo Finance, via `yfinance`                                                                |
| FOMC meeting dates                                                                    | [Federal Reserve calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) |
| Official target, yields, VIX, credit spread, CPI, unemployment, industrial production | [FRED](https://fred.stlouisfed.org)                                                          |
| Foreign indices, used only to assess synthetic control                                | Yahoo Finance                                                                                |


Every value on a date is what was known by that close. All 92 target changes since 1994 match the Fed's [own list](https://www.federalreserve.gov/monetarypolicy/openmarket.htm).

## Design


| Step           | Choice                                                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unit           | One FOMC decision, February 1994 to October 2026                                                                                                  |
| Treatment      | Hike vs hold (52 vs 179); the 40 cuts are exploratory                                                                                             |
| Outcomes       | S&amp;P 500 price return from the close before the decision to 1 and to 21 trading days after it                                                  |
| Effect         | ATT, for all hikes and for contested hikes, where comparable holds exist                                                                          |
| Method         | Observational study: regression, standardisation, inverse-odds weighting                                                                          |
| Key assumption | Conditional exchangeability, given market expectations, the policy path, the Fed's mandate and the market state                                   |
| Checks         | Simulation with a known effect, other controls and subsets, influence, fake dates, lead test, circular shifts, sensitivity to a hidden confounder |


## How this could be improved

Checks on the current analysis (full walkthrough in
[`validation/README.md`](validation/README.md)) point to one underlying limitation: both
hikes and cuts are highly predictable from public information (AUC 0.86 and 0.988), so the
binary hike/hold/cut treatment barely varies in the region that matters, and the sample is too
small to detect a plausible effect at the 21-day horizon. A future, pre-registered study —
not a re-analysis of this one — could address this on three fronts:

1. **Size the study to the effect.** The regression can only reliably detect an effect of
 about 4 points at 21 days, against a plausible true effect of 1–3 points. A follow-up should
 size its horizon and sample to a target effect from the outset, rather than choosing a
 horizon for business relevance and discovering afterward that it's underpowered.
2. **Use a surprise-based treatment.** Replacing the binary hike/hold/cut label with the
 market-implied surprise around the announcement (e.g. from Fed funds futures, Kuttner 2001)
 uses the variation a binary label throws away, and would let cuts be analyzed too — they
 currently can't be, since 27 of 40 cuts have almost no comparable hold. This reframes the
 research question (a dose-response slope, not a discrete comparison) rather than patching
 this one, so it would mean rewriting the question, not just swapping an estimator.
3. **Separate the policy move from the information it carries.** Decomposing the surprise
 into a pure policy component and a "Fed information" component (Jarociński &amp; Karadi,
 2020; Nakamura &amp; Steinsson, 2018) would avoid attributing a surprise that is really the
 Fed signalling bad news about the economy to the policy action itself.

Independent of data access, a further option is to pre-register predictions for a fixed
number of future meetings and score them prospectively as they occur, since the Fed's meeting
schedule is public and set years in advance — rather than relying only on a backward-looking
historical sample.

## Deadline

Report and notebook are due **one week before** the oral presentation. No changes are accepted after that date.