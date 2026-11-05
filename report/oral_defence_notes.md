# Oral defence notes

For your preparation only; this is not part of the submission. Read the report first, then try each question aloud without looking at the answer.

## Your pitch in 60 seconds

Headlines say stocks fell because the Fed hiked, but the Fed does not choose at random. So I treated each FOMC decision since 1994 as a unit and compared 52 hikes with 179 holds, using only what was known the day before. The hard part is that markets anticipate: the day before, a hike is often close to certain, so about half of all hikes have no comparable hold. I fixed a rule in advance for claiming an effect. In the first two days I find nothing. Over the next month every method points to a lower return, roughly one to three points, but no interval excludes zero, and one crisis meeting moves the main estimate by a full point. So I claim an association, not a causal effect, and I recommend treating a lower month as a stress scenario, not a forecast.

## Numbers to know

| What | Value |
|---|---|
| Decisions | 52 hikes, 179 holds, 40 cuts (271 in all) |
| 2-day regression | −0.31 (−1.11 to +0.49) |
| 21-day regression | −2.94 (−6.01 to +0.13), p = 0.032 |
| 21-day naive gap | −1.13 (−2.42 to +0.15) |
| All 21-day estimates | −1.13 to −3.22 |
| Contested hikes only | −1.21 to −2.44 |
| Without 16 September 2008 | −1.91 |
| Predictability the day before | AUC 0.97 with market expectations, 0.86 without |
| Effective hold meetings | 11 with market expectations, 28 without |
| Hikes with no comparable hold | 25 of 52 |
| Fake date, 21-day | −0.78 raw, +0.22 adjusted |
| Smallest detectable effect | 1.1 points at 2 days, 4.2 at 21 days |

## Likely questions

**Why not difference-in-differences?**
A decision hits the whole index at once, so there is no untreated group. DiD removes shocks common to both groups, and here the common shock is the effect I want. Comparing sectors would measure relative effects, not the index.

**Why not synthetic control? You do have one treated unit.**
It needs one clean intervention and donors the treatment does not touch. The Fed decides eight times a year, so there is no clean "before". Foreign markets carry the US decision-day move into their next session, clearly in Asia, and other central banks tightened at the same time in 2022.

**Why the ATT and not the ATE?**
A hike in mid-crisis was never on the table, so the ATE asks about a world with no data. The ATT needs comparable holds only for meetings where the Fed hiked, and it answers the question people ask about a real hike.

**What is your key assumption, and how could it fail?**
Conditional exchangeability: among meetings with the same controls, whether the Fed hiked is unrelated to what the S&P would have done under a hold. It fails if the Fed knows something markets do not, or if other news arrives in the window. It cannot be tested directly, so I tried to break it with placebos and measured how strong a hidden factor would need to be.

**Market expectations come from yields. Isn't that controlling for something the Fed affects?**
They are measured the day before the decision, so the decision cannot have caused them. Yields *after* the decision are mediators, and I never adjust for those.

**Why do expectations matter so much?**
Prices already include what markets expect. If a hike is expected with probability p, a hike surprises by 1 − p and a hold by p in the other direction, so both potential outcomes rise with p. Since p is high at hike meetings, leaving it out understates a negative effect. The 21-day regression moves from −1.73 to −2.94 when I add expectations.

**What does "contested" mean, and why report it?**
A hike with a propensity below 0.9, so a hold was still realistic. Above 0.9 there are 25 hikes and no holds at all, a positivity problem. For those hikes, any estimate is an extrapolation.

**Why do regression and weighting disagree?**
They aim at different groups and use different assumptions. Regression and standardisation for all hikes extrapolate with a linear model, so they can reach hikes with no comparable holds, and their estimates are larger. Weighting cannot extrapolate, so it relies on about 11 effective holds and is noisier.

**Why regression as the headline if it extrapolates?**
It is the guide's recipe and it had the lowest error in my simulation with a known effect, even when anticipation pulled it toward zero. I report contested-hike estimates beside it so that the reader sees the difference.

**Why 97.5% intervals?**
I test two horizons, so Bonferroni gives 2.5% each (Session 2).

**Why HC3? With clustering your 21-day result is significant.**
That is true: clustered by year, the 95% interval is −4.86 to −1.02. I fixed HC3 in advance, and it is the cautious choice because a few meetings have high leverage, up to 0.63. Switching after seeing the result would be exactly the problem the plan exists to prevent. The difference is reported.

**Why keep 16 September 2008? It looks like an outlier.**
Dropping it because of what happened after it would be selecting on the outcome. The plan keeps it, and I report that without it the estimate is −1.91. Its extreme yields tilt the regression.

**So is the answer "no effect"?**
No. At 21 days the placebos pass, and the result fails for lack of precision. The regression can reliably detect only about 4.2 points or more, so a real effect of 2 points could easily go undetected. No evidence of an effect is different from evidence of no effect.

**What do the placebos show?**
A decision cannot cause a return before it. The raw gap is already −0.78 in the window before the decision, so the raw comparison is partly about regimes. With controls that gap becomes +0.22, which supports the adjusted estimate over the raw one.

**Why start in 1994?**
4 February 1994 is the first time a decision was announced right after the meeting. Before that, markets had to infer decisions, so the treatment date was not clear.

**Why 21 days?**
It is about a month, a horizon a company cares about, and about 95% of those windows close before the next decision, so a later decision does not contaminate them. The 2-day window is the sharp test.

**How did you avoid look-ahead bias?**
Market variables come from the previous close. Macro variables count only once published: last month's figures from the 20th, otherwise those of the month before. They are revised figures, not first releases, and I state that as a limit.

**Why not use monthly data?**
Since 2000 the monthly rule marks 136 increases against 41 real hikes, 126 of 393 months since 1994 had no decision, and a next-month return misses a mid-month reaction.

**The guide says Kaggle. Why a merged file?**
No single Kaggle file has decision dates and market yields. The outcome comes from a Kaggle S&P 500 dataset, the rest from public sources, all merged into one documented CSV. Say what your instructor agreed to here.

**You looked at the data before freezing the plan. Isn't that a problem?**
Yes, it is a limit, so I disclose it. An earlier test run looked at several windows and estimators. After that I chose the propensity model without using post-decision returns, and I froze the estimators and the claim rule in git before the final run. Anything added later, such as the influence checks, is labelled.

**What would make this study stronger?**
Fed funds futures, to measure how far each decision differed from what markets expected. That is where the literature finds the effect: about 1% for a surprise 25 basis point cut (Bernanke and Kuttner, 2005).

**What do you recommend to the company?**
Do not act on an announced hike by itself. Treat a lower return of a few points in the following month as a stress scenario, not a forecast, and watch how far a decision differs from what markets expected.

## Things to be able to do at the board

- Write gap = ATT + selection bias, and say what each term means for the hike of 16 March 2022.
- Draw the causal graph, and label which arrows you block and which you leave open.
- Explain why a propensity near 1 is a problem for the ATT.
- Explain why regression leans on contested meetings, using Frisch-Waugh-Lovell.
