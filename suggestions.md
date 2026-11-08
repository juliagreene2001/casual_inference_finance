# Suggestions

Findings from validating the project, for the original author to review.

## 1. Replace the Kaggle S&P 500 download with `yfinance`

**Current:** `scripts/build_dataset.py` downloads S&P 500 closes from a Kaggle dataset
(`paveljurke/s-and-p-500-gspc-historical-data`). `yfinance` is already a dependency,
used only for the foreign donor indices.

**Why it was done this way:** the project guide originally required a Kaggle dataset.
That requirement has since been confirmed as not mandatory.

**Validation:** compared the Kaggle-sourced `sp500_close` column against a direct
`yfinance.download("^GSPC")` pull over the full date range (`validation/sp500_source_comparison.py`).

- 11,111 trading days in both sources, same date coverage
- Largest gap: 0.00001% (float rounding only)

**Suggestion:** drop the Kaggle download step and source S&P 500 closes from
`yfinance` directly, like the donor indices already are. Removes a manual dataset
dependency with no change to the data or results. See
`validation/sp500_source_comparison.py` and `validation/sp500_source_comparison.csv`.

## 2. Make the regression's extrapolation explicit, and consider a co-headline

**Current:** the regression estimate is reported as the headline at both horizons, even
though (by Frisch-Waugh-Lovell) it's implicitly weighted toward the "contested" hikes and
extrapolates to the 25 of 52 hikes with no comparable hold at all. The contested-only
standardisation/weighting numbers are reported, but as secondary rows next to regression,
not as a co-headline.

**Why it matters:** at 21 days this isn't cosmetic. From the notebook's saved results
(`results/numbers.json` / Cell 16's output):

| Horizon | Regression (all hikes, extrapolated) | Standardisation, contested | Overlap weighting |
|----|---|---|---|
| 2-day   | −0.31 [−1.11, +0.49] | −0.38 [−1.10, +0.64] | −0.21 [−1.01, +0.60] |
| 21-day  | **−2.94** [−6.01, +0.13] | −2.44 [−5.75, +0.23] | −1.39 [−3.57, +0.78] |

Standardisation on *all* hikes (−3.22) is even more extreme than regression — both lean on
units with no real counterfactual. Restricting to contested hikes pulls the estimate back
closer to zero and widens the interval, which is itself informative: a large chunk of the
headline number is coming from extrapolation, not from meetings where a hold was actually
plausible.

**Suggestion:** state this tradeoff explicitly in the report (Results or Checks section) —
not just that regression is "the guide's recipe," but that its headline number is partly an
extrapolation, with the contested-only numbers given equal visual weight as a check on how
much that extrapolation matters.

**Validated with an additional method:** `validation/overlap_weighting_estimate.py`
(+ `validation/overlap_weighting_results.csv`) implements overlap weighting
(Li, Morgan & Zaslavsky, 2018) — weighting each hike by `1 - e(X)` and each hold by `e(X)` instead of
hard-cutting at propensity 0.9. It avoids the arbitrary "contested" threshold entirely.
Result: −0.21 [−1.01, +0.60] at 2 days, −1.39 [−3.57, +0.78] at 21 days — closer to the
naive gap than to regression, and does not exclude zero at either horizon. This supports
the suggestion above: the further a method leans on extrapolation (regression > hard-cutoff
contested > overlap weighting), the larger the estimate gets, and the smoothest, least
extrapolation-dependent method agrees with "no effect credibly detected."

*Corrected after review: the first version gave every meeting the same weight `e(X)(1-e(X))`,
which leaves hikes and holds unbalanced, and reported −0.12 and −1.33. The notebook repeats
this check in Section 6.6, refitting the propensity inside a year-block bootstrap:
−0.21 [−1.03, +0.70] at 2 days and −1.47 [−3.82, +0.19] at 21 days.*

## 3. Propose a follow-up study designed around the power problem

**Current:** the simulation (Step 6.1) shows the regression's power at 21 days is very low —
it can only reliably detect an effect of about 4.2 points, against a plausible true effect of
1-3 points (per the literature cited in the project's own oral-defence notes: Bernanke &
Kuttner 2005 find ~1% for a surprise 25bp move). This isn't fixable by re-analyzing the same
data differently — the 2-day/21-day horizons were pre-registered for good reasons (sharp test;
contamination control) and can't be swapped post-hoc without reintroducing the multiple-testing
problem the plan was designed to avoid.

**Suggestion:** propose a follow-up study, pre-registered in advance, that:
1. **Sizes the horizon/sample to the effect**, using the course's planning formula
   (`n ~ 2*sigma^2*(z_1-a/2 + z_1-b)^2 / delta^2`) with a target effect size from the
   literature, rather than choosing a horizon for substantive relevance alone and discovering
   after the fact that it's underpowered.
2. **Uses a surprise-based treatment** (the change in Fed funds futures prices in a narrow
   window around the announcement) instead of a binary hike/hold label. This directly targets
   the project's biggest overlap problem — half of all hikes are already near-certain the day
   before, so "hike vs. hold" barely varies in the region that matters; a continuous surprise
   measure uses that variation instead of discarding it.

   **Caveat: this changes the question, not just the method.** The original estimand is
   `E[Y(hike) - Y(hold)]` — the effect of the Fed's discrete decision. A surprise-based design
   estimates `dY/d(surprise)` — the market's response per unit of unanticipated policy news,
   a dose-response slope, not a discrete comparison. These aren't the same quantity: a hike
   that was 95% priced in and a hike that blindsides the market are both "hike = 1" under the
   original design, but very different surprise magnitudes. Under market efficiency the two
   are related (an anticipated hike should move prices ~0, so the whole reaction should come
   from the surprise component), but adopting this design means rewriting Step 1's question
   from "does a hike move the market vs. a hold" to "how much does the market move per unit of
   policy surprise" — a different, arguably better-posed question, not a drop-in fix to the
   original one. A lesser version of this is already implicit in the project: "contested"
   hikes (low propensity, comparable holds exist) are, almost by definition, the less
   predictable ones — closer to high-surprise hikes — so the propensity-restricted and
   overlap-weighted estimates already computed are a crude, binary approximation of what a
   surprise regression would do continuously.

**Validated — but only for the study as it already ran.** `validation/power_sizing_check.py`
(+ `validation/power_sizing_results.csv`) runs the course's planning formula across every
horizon already in the data, using the real hold-group standard deviation and the real sample
size (52 hikes). This describes the existing study's power at each horizon; it does **not**
simulate or validate a hypothetical surprise-based study — there's no Fed funds futures data
here to do that with, so point 2 above remains a proposal, not something checked.

| Horizon | Hikes/Holds | Hold-group SD | MDE at current n | N/arm needed for 1pt | N/arm needed for 2pt | N/arm needed for 3pt |
|---|---|---|---|---|---|---|
| 0-day | 52/179 | 1.03 | 0.62 | 20 | 5 | 2 |
| 2-day (used) | 52/179 | 1.58 | 0.96 | 47 | 12 | 5 |
| 5-day | 52/178 | 2.27 | 1.37 | 98 | 25 | 11 |
| 10-day | 52/178 | 2.72 | 1.64 | 140 | 35 | 16 |
| **21-day (used)** | 52/178 | 4.22 | **2.55** | 338 | 85 | 38 |
| 42-day | 51/178 | 6.02 | 3.68 | 689 | 172 | 77 |
| 63-day | 51/178 | 7.06 | 4.31 | 946 | 237 | 105 |

Power falls off fast as the horizon lengthens, because return volatility grows with it — the
already-chosen 2-day "sharp test" is in fact close to optimally powered for a ~1-point effect,
while 21-day (chosen for business relevance, not power) is the horizon that struggles. Note
this table's MDE (2.55 at 21 days) is still *lower* than the notebook's own regression-based
figure (4.2) — the gap is the overlap problem from Step 4: the effective number of comparable
holds (Kish ESS) is only 11-28, not 178, and this simplified two-group formula doesn't capture
that shrinkage. A real follow-up study would need to address overlap (e.g. point 2 above), not
just add more calendar years of data at the 21-day horizon.
