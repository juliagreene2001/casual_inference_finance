"""Build report/fed_sp500_report.pdf from the notebook's saved results.

Run the notebook first, then `uv run python report/build_report.py`. Every number in
the prose comes from results/numbers.json or the results/ tables, so the report
cannot drift from the notebook. To change the company link, edit COMPANY_LINK below.
"""

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUTPUT = ROOT / "report" / "fed_sp500_report.pdf"
FONTS = Path("/System/Library/Fonts/Supplemental")

AUTHOR = "Ali Vakof"
COMPANY_LINK = (
    "<b>Link to a company.</b> A company treasury with stock-market exposure, or one planning a share issue, "
    "must decide whether to hedge or to wait when a hike approaches. It cannot change the Fed's decision, only "
    "its own reaction. So it needs exactly this number: what a real hike does compared with no hike. We use "
    "2 points over a month as an illustrative threshold for acting; a real treasury would set its own from its costs."
)
COMPANY_THRESHOLD = 2

n = json.loads((RESULTS / "numbers.json").read_text())
main = pd.read_csv(RESULTS / "table_main.csv")
strata = pd.read_csv(RESULTS / "table_strata.csv")
falsification = pd.read_csv(RESULTS / "table_falsification.csv")
checks = pd.read_csv(RESULTS / "table_checks.csv")
influence = pd.read_csv(RESULTS / "table_influence.csv", parse_dates=["date"])
sim = n["simulation"]


def num(value, digits=2):
    """Number with a true minus sign."""
    return f"{value:.{digits}f}".replace("-", "−")


def signed(value, digits=2):
    return f"{value:+.{digits}f}".replace("-", "−")


def between(low, high):
    return f"{signed(low)} to {signed(high)}"


def estimate(key):
    """Estimate and interval from the main table, in running text."""
    value, low, high = n["main"][key]
    return f"{num(value)} ({between(low, high)})"


def estimate_sentence(key):
    value, low, high = n["main"][key]
    return f"{num(value)} points, with a 97.5% interval of {between(low, high)}"


def check(y, name):
    return n["checks"][f"{y}|{name}"]


def group_range(y, group):
    values = checks[(checks["Outcome"] == y) & (checks["Group"] == group)]["Estimate"]
    return values.min(), values.max()


def fake(horizon, test, column):
    return n["falsification"][f"{horizon}|{test}"][column]


estimates_21 = [n["main"][k][0] for k in n["main"] if k.startswith("21-day")]
estimates_2 = [n["main"][k][0] for k in n["main"] if k.startswith("2-day")]
contested_21 = [n["main"][f"21-day|{m}"][0] for m in ["Standardisation, contested", "Weighting, contested", "Within bands, contested"]]
controls_low, controls_high = group_range("y21", "Control set")
cycle_low, cycle_high = group_range("y21", "Leave a cycle out")
subset_low, subset_high = group_range("y21", "Subset")
sens = n["sensitivity"]["21-day"]
top = n["influence_y21"]
without_top = check("y21", "Without the most influential meeting")
without_five = check("y21", "Without the 5 most influential meetings")
capped = check("y21", "Largest 2% of returns capped")
clustered = check("y21", "Clustered by year")
same_year = check("y21", "Same calendar year only")
no_expectations = check("y21", "All except expectations")
assert not n["rule"]["2-day"]["claim_causal"] and not n["rule"]["21-day"]["claim_causal"], "The prose below assumes no causal claim."
assert all(v < 0 for v in estimates_21) and all(v < 0 for v in estimates_2), "The prose below assumes all estimates are negative."
assert all(row["Low"] < 0 < row["High"] for _, row in main.iterrows()), "The prose below assumes every interval includes zero."
two_day = checks[checks["Outcome"] == "y1"]
assert ((two_day["Low"] < 0) & (two_day["High"] > 0)).all(), "The prose below assumes every 2-day check includes zero."
assert (checks[checks["Outcome"] == "y21"]["Estimate"] < 0).all(), "The prose below assumes no 21-day check changes sign."
assert n["n_cycles"] == 7 and n["n_controls"] == 18 and top["top_date"] == "2008-09-16", "The prose names these directly."

# ----- Fonts and styles
for name, file in [("Body", "Times New Roman.ttf"), ("Body-Bold", "Times New Roman Bold.ttf"), ("Body-Italic", "Times New Roman Italic.ttf"),
                   ("Body-BoldItalic", "Times New Roman Bold Italic.ttf"), ("Sans", "Arial.ttf"), ("Sans-Bold", "Arial Bold.ttf"),
                   ("Sans-Italic", "Arial Italic.ttf"), ("Sym", "Arial Unicode.ttf")]:
    pdfmetrics.registerFont(TTFont(name, FONTS / file))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic")
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-Italic", boldItalic="Sans-Bold")

INK = colors.HexColor("#0b0b0b")
SECONDARY = colors.HexColor("#52514e")
RULE = colors.HexColor("#c3c2b7")
WASH = colors.HexColor("#f4f3ef")

BODY = ParagraphStyle("body", fontName="Body", fontSize=11, leading=13.9, alignment=TA_JUSTIFY, spaceAfter=6, textColor=INK)
LIST_ITEM = ParagraphStyle("item", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2.5, bulletFontName="Body", bulletFontSize=11)
EQUATION = ParagraphStyle("eq", parent=BODY, alignment=TA_CENTER, spaceBefore=1, spaceAfter=6)
TITLE = ParagraphStyle("title", fontName="Sans-Bold", fontSize=19, leading=23, textColor=INK, spaceAfter=3)
SUBTITLE = ParagraphStyle("subtitle", fontName="Sans", fontSize=11, leading=14, textColor=SECONDARY, spaceAfter=3)
BYLINE = ParagraphStyle("byline", fontName="Sans", fontSize=8.8, leading=12, textColor=SECONDARY, spaceAfter=8)
H1 = ParagraphStyle("h1", fontName="Sans-Bold", fontSize=12.2, leading=15, textColor=INK, spaceBefore=9, spaceAfter=4, keepWithNext=1)
CAPTION = ParagraphStyle("caption", fontName="Sans", fontSize=8.2, leading=10.3, textColor=SECONDARY, spaceBefore=2, spaceAfter=9, alignment=TA_LEFT)
TABLE_TITLE = ParagraphStyle("tabletitle", fontName="Sans-Bold", fontSize=8.6, leading=11, textColor=INK, spaceBefore=4, spaceAfter=3, keepWithNext=1)
CELL = ParagraphStyle("cell", fontName="Sans", fontSize=8, leading=9.9, textColor=INK)
CELL_BOLD = ParagraphStyle("cellbold", parent=CELL, fontName="Sans-Bold")
BOX = ParagraphStyle("box", parent=BODY, fontName="Body", fontSize=10.8, leading=13.6, spaceAfter=0)
REF = ParagraphStyle("ref", parent=BODY, fontSize=8.8, leading=10.7, leftIndent=11, firstLineIndent=-11, spaceAfter=1.6, alignment=TA_LEFT)

WIDTH = A4[0] - 2 * 2.1 * cm


def clean(text):
    return text.replace("S&P", "S&amp;P").replace("<sub>", '<sub rise="2.4" size="8">')


def para(text, style=BODY):
    return Paragraph(clean(text), style)


def bullet(text):
    return Paragraph(clean(text), LIST_ITEM, bulletText="•")


def figure(file, caption, width=WIDTH):
    path = RESULTS / file
    w, h = ImageReader(str(path)).getSize()
    return KeepTogether([Image(str(path), width=width, height=width * h / w), para(caption, CAPTION)])


def table(title, rows, widths, numeric_from=None, bold_rows=(), note=None):
    cells = []
    for i, row in enumerate(rows):
        style = CELL_BOLD if i == 0 or i in bold_rows else CELL
        cells.append([Paragraph(clean(str(value)), style) for value in row])
    grid = Table(cells, colWidths=[w * WIDTH for w in widths], repeatRows=1, hAlign="LEFT")
    grid.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK), ("LINEBELOW", (0, -1), (-1, -1), 0.8, INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, RULE),
    ]))
    parts = [para(title, TABLE_TITLE), grid]
    parts.append(para(note, CAPTION) if note else Spacer(1, 7))
    return KeepTogether(parts)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Sans", 8)
    canvas.setFillColor(SECONDARY)
    canvas.drawString(2.1 * cm, 1.15 * cm, "Does a Fed rate hike move the S&P 500?")
    canvas.drawRightString(A4[0] - 2.1 * cm, 1.15 * cm, str(doc.page))
    canvas.restoreState()


story = []

# ----- Title and summary
story += [
    para("Does a Fed Rate Hike Move the S&P 500?", TITLE),
    para("An observational study of FOMC decisions, February 1994 to October 2026", SUBTITLE),
    para(f"{AUTHOR} · M2 Causal Inference · Albert School · Instructor: Alassane Diallo · November 2026", BYLINE),
]
brief = Table([[para(
    f"<b>In brief.</b> When the Fed raises rates, how much does the S&P 500 move compared with what it would have done had the Fed held? "
    f"We compare {n['n_hike']} hikes with {n['n_hold']} holds, using only what was known the day before each decision. Over the first two days "
    f"we detect no effect: {estimate_sentence('2-day|Regression')}. Over the following month, every method "
    f"points to a lower return, between {num(max(estimates_21))} and {num(min(estimates_21))} points, but every interval includes zero, and "
    f"removing one crisis meeting moves the main estimate from {num(n['main']['21-day|Regression'][0])} to {num(without_top[0])}. By the rule we fixed "
    f"before the final run, we do not claim a causal effect at either horizon. The practical reading: the average hike is not news on the day, "
    f"because markets mostly expect it, and a lower month of a few points is a scenario to plan for, not a forecast.", BOX)]], colWidths=[WIDTH])
brief.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), WASH), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
story += [brief, Spacer(1, 4)]

# ----- 1. Introduction
story += [
    para("1. Introduction", H1),
    para("The federal funds rate is the most closely watched price in finance. After each meeting of the Federal Open Market Committee (FOMC), headlines "
         "link the decision to the stock market. Those links are correlations. The Fed does not choose at random: it raises rates when inflation is high "
         "and the economy is strong, and it cuts when trouble arrives. Comparing markets after different decisions is like comparing fires by the number of "
         "firefighters present: the firefighters arrive where the fire is."),
    para("<b>The causal question.</b> In meetings where the Fed raised its target, how different would the S&P 500 return have been if it had held instead?"),
    bullet("<b>Unit:</b> one FOMC decision, February 1994 to October 2026."),
    bullet(f"<b>Treatment:</b> hike (<i>T</i> = 1) or hold (<i>T</i> = 0), read from the official target. The {n['n_cut']} cuts are analysed separately."),
    bullet("<b>Outcome:</b> the S&P 500 price return from the close before the decision to the close one trading day after it (“2-day”, the sharp test) "
           "and to the close 21 trading days after it (“21-day”, the business horizon). Effects are in percentage points of return, or “points”."),
    Spacer(1, 3),
    para("<b>Whose effect?</b> Each meeting has two possible outcomes, and we want an average of their difference. The ATE averages over all meetings, including "
         "mid-crisis meetings where a hike was never on the table, so no data speaks to it. The ATU asks what a hike would have done at meetings where the Fed held. "
         "The ATT asks about meetings where the Fed actually hiked, and it is our target:"),
    para("ATT = E[ <i>Y</i>(1) − <i>Y</i>(0) | <i>T</i> = 1 ]", EQUATION),
    para("It is the question a decision-maker asks about a real hike, and it asks less of the data: we rebuild the missing no-hike world only for hikes, so we need "
         "comparable holds only for them (Session 1, slide 49)."),
    para(COMPANY_LINK),
]

# ----- 2. Data
sources = [
    ["Content", "Source", "Used for"],
    ["S&P 500 daily closes", "Kaggle: <i>S&P 500 (^GSPC) Historical Data</i>, by paveljurke", "Outcome, market state"],
    ["FOMC meeting dates", "Federal Reserve meeting calendars", "Decision dates"],
    ["Official target; Treasury yields; VIX; credit spread; CPI; unemployment; industrial production", "FRED, St. Louis Fed", "Treatment, controls"],
    ["Foreign stock indices", "Yahoo Finance", "Testing synthetic control"],
]
story += [
    para("2. Data", H1),
    para(f"<b>One file.</b> All the data sit in one CSV of {n['n_rows']:,} trading days and {n['n_columns']} columns, merged once from the sources in Table 1 and then frozen: S&P closes, the target and decision label, Treasury yields, VIX, credit spread, inflation, unemployment, industrial production and foreign indices. "
         "Table 2 gives each variable its role. The notebook reads only this file and downloads nothing, so its results cannot change. We checked the file against sources not used to build it: all 92 rate changes since 1994 "
         "match the Fed's own list, the 63 changes through March 2017 match a second Kaggle dataset, and S&P closes match Yahoo Finance."),
    table("Table 1. Data sources (URLs and the 5 November 2026 download date are in the notebook's first cell)", sources, [0.44, 0.38, 0.18]),
    para(f"<b>How the treatment was assigned.</b> The FOMC meets eight times a year and votes on the target; in rare cases it acts between meetings. Its mandate is maximum "
         f"employment and stable prices, so decisions depend on inflation, employment and financial conditions, all measured here. The Committee also tends to avoid surprising "
         f"markets, which is why market expectations matter. We start on 4 February 1994, the first time a decision was announced right after the meeting; before that, markets "
         f"had to infer decisions (Poole and Rasche, 2003). That gives {n['n_decisions']} decisions: {n['n_hike']} hikes, {n['n_hold']} holds and {n['n_cut']} cuts."),
    para("<b>Time order.</b> Controls must come before the decision and returns after it. Market variables are read at the previous close. Macro variables count only once "
         "published: last month's figures from the 20th onward, otherwise those of the month before. We use today's revised figures, not first releases, which is a limit. CPI and "
         "unemployment for October 2025 were never published, so the last known values carry forward."),
    para(f"<b>Why decisions and not months.</b> This project began with monthly data, and an audit showed why that fails. Since 2000 a monthly-average rule marks "
         f"{n['audit_increase_months']} months as rate increases, but the Fed hiked only {n['audit_real_hikes']} times, because one hike lifts the average across two months. Since 1994, "
         f"{n['audit_months_no_decision']} of {n['audit_months_since_1994']} months contained no decision at all, so “no increase” mixes holds, cuts and months with no meeting. "
         f"And a hike on 15 March moves prices on 15 March, while a next-month return starts at the end of March. That design gave {num(n['old_design_est'])} (standard error {num(n['old_design_se'])}), "
         f"which says nothing. Since 1982, regressing the level of the S&P on the level of the rate looks impressive (<i>t</i> = {num(n['levels_t'], 1)}, <i>R</i><super>2</super> = {num(n['levels_r2'])}), "
         f"but a Durbin-Watson statistic of {num(n['levels_dw'], 3)} is the classic sign of a spurious link between two trending series. In changes, the <i>R</i><super>2</super> is essentially zero."),
    figure("fig1_timeline.png", "<b>Figure 1.</b> The Fed target with every hike and cut decision, and the S&P 500, 1994 to 2026."),
]

# ----- 3. Causal framework
roles = [
    ["Role", "Variables", "Rule"],
    ["Confounders (X): Fed's mandate", "Inflation, unemployment and its 3-month change, industrial production growth, as last published", "Adjust"],
    ["Confounders (X): policy path", "Last decision was a hike or a cut; hikes and cuts in the past 12 months; target level", "Adjust"],
    ["Confounders (X): market state", "S&P return over the past 21 and 252 days, VIX, credit spread, 10-year minus 3-month yield", "Adjust"],
    ["Confounders (E): expectations", "3-month, 1-year and 2-year yields minus the target; 21-day change in the 3-month yield", "Adjust"],
    ["Mediators (M)", "Yields, VIX and credit after the decision; later macro data; the next decision", "Never adjust"],
    ["Hidden (U)", "The Fed's private information; surprise news during the window", "Sensitivity analysis"],
]
story += [
    para("3. Causal framework", H1),
    para(f"<b>Potential outcomes.</b> At each meeting <i>i</i> there are two possible worlds: <i>Y<sub>i</sub></i>(1), the S&P return if the Fed hikes, and <i>Y<sub>i</sub></i>(0), the return if it holds. "
         f"On 16 March 2022 the Fed hiked, and the S&P gained {num(n['example_y21'], 1)}% over the next 21 trading days. That is <i>Y</i>(1). What it would have done under a hold, <i>Y</i>(0), is missing forever: "
         f"no dataset can record it (Holland, 1986). So the whole project is one job: rebuild E[<i>Y</i>(0) | <i>T</i> = 1], what hike meetings would have looked like under a hold."),
    para(f"<b>Why the raw comparison is unfair.</b> The S&P gained {num(n['mean_hike_y21'])}% on average in the window after a hike and {num(n['mean_hold_y21'])}% after a hold, a raw gap of "
         f"{num(n['main']['21-day|Naive gap'][0])} points. Session 1 shows that this gap mixes two things:"),
    para("Raw gap = ATT + ( E[ <i>Y</i>(0) | <i>T</i> = 1 ] − E[ <i>Y</i>(0) | <i>T</i> = 0 ] ), where the bracket is selection bias.", EQUATION),
    para(f"Selection bias is not zero, because the two groups of meetings live in different economies. Inflation averaged {num(n['mean_hike_inflation'], 1)}% at hike meetings and "
         f"{num(n['mean_hold_inflation'], 1)}% at holds; unemployment averaged {num(n['mean_hike_unemployment'], 1)}% and {num(n['mean_hold_unemployment'], 1)}%. Figure 2 sets out our causal story, and Table 2 gives each variable its role."),
    figure("fig2_dag.png", "<b>Figure 2.</b> Causal graph. An arrow means “changing this could change that”. Orange: the effect we want, so we never adjust for M. "
           "Solid grey: back-door paths, which we close by adjusting for X and E. Dashed: hidden paths, which data cannot close.", width=WIDTH * 0.86),
    table("Table 2. Variables and their roles", roles, [0.27, 0.57, 0.16]),
    para(f"<b>Expectations are the subtle confounder.</b> Prices already include what markets expect. If a hike is expected with probability <i>p</i>, a hike surprises markets by 1 − <i>p</i>, and a hold "
         f"surprises them by <i>p</i> in the other direction. So both potential outcomes rise with <i>p</i>, and <i>p</i> is high at hike meetings. That makes the raw gap understate a true negative effect. "
         f"Our results fit this: the 21-day regression is {num(no_expectations[0])} without expectations and {num(n['main']['21-day|Regression'][0])} with them."),
    para("<b>What we do not control for.</b> Yields and volatility after the decision are mediators, so controlling for them would remove part of the effect. We also define the main sample and the subsets "
         "by calendar or pre-decision information, never by what happened afterwards: dropping “crash months” would select on a consequence, which can invent patterns as a collider does. The influence checks in Section 7 "
         "drop individual meetings only to show how much they matter, and they do not replace the headline."),
    para("<b>The assumptions</b> an estimate needs before it can be read causally:"),
    bullet(f"<b>Consistency.</b> “Hike” must mean one treatment. Sizes run from 25 to {int(n['largest_hike'] * 100)} basis points ({n['hikes_25bp']} of {n['n_hike']} are 25), and holds near zero rates came with quantitative easing. We test both."),
    bullet("<b>Conditional exchangeability.</b> <i>Y</i>(0) <font name='Sym'>⊥</font> <i>T</i> | <i>X</i>: among meetings with the same controls, whether the Fed hiked is unrelated to what the S&P would have done under a hold. "
           "No data can prove this, so Section 7 tries to break it."),
    bullet("<b>Positivity.</b> Comparable holds must exist for each hike. Section 5 shows that this holds for only about half of them."),
    bullet(f"<b>No interference.</b> One meeting's decision should not change another meeting's window. About {100 - n['share_21d_reach_next']:.0f}% of 21-day windows end before the next decision, but past hikes may still affect later returns."),
]

# ----- 4. Method
donors = n["donor_pass"]
tree = [
    ["The guide's question", "Answer", "Why"],
    ["Randomly assigned?", "No", "The FOMC decides, based on the economy."],
    ["Several treated units, before and after?", "No", "A decision hits the whole index at once. DiD removes “shocks common to both groups” (Session 3), and here the common shock is the effect we want. A sector DiD would answer a different question: relative effects, not the index."],
    ["One treated unit, before and after?", "Looks like yes, but fails",
     f"Synthetic control needs one clean intervention and donors the treatment does not touch. The Fed decides eight times a year, so there is no clean “before”. Foreign indices correlate {num(n['donor_corr_min'])} to {num(n['donor_corr_max'])} with the S&P. "
     f"Markets closed at the announcement carry the US decision-day move into their next session: clearly in Asia (per point: Hang Seng {num(donors['Hang Seng'][0])}, ASX {num(donors['ASX 200'][0])}, Nikkei {num(donors['Nikkei 225'][0])}), more weakly in Europe (about {num(donors['FTSE 100'][0], 1)}). "
     "Other central banks were also tightening in 2022, and US policy moves risky assets worldwide (Miranda-Agrippino and Rey, 2020). The donors are not untouched."],
    ["Main confounders observed?", "<b>Yes</b>", "The Fed's mandate makes the assignment story public, and we observe its main inputs. So this is an <b>observational study</b>."],
]
story += [
    para("4. Method", H1),
    table("Table 3. Choosing the method: ask in order, the first “yes” wins", tree, [0.21, 0.10, 0.69]),
    para("<b>Key assumption.</b> Conditional exchangeability, as stated above. Angrist, Jordà and Kuersteiner (2018) use the same selection-on-observables logic for FOMC decisions, which gives this design a published precedent. "
         "Instrumental variables appear in Session 4, but the guide does not allow them here."),
    para("<b>Four ways to build the missing world,</b> from simplest up:"),
    bullet("<b>Naive gap:</b> hike mean minus hold mean. This is the ATT plus selection bias."),
    bullet(f"<b>Regression (headline):</b> <i>Y<sub>i</sub></i> = α + β<i>T<sub>i</sub></i> + <i>X<sub>i</sub></i>′γ + ε<i><sub>i</sub></i>, with the {n['n_controls']} controls in Table 2, the guide's recipe. By Frisch-Waugh-Lovell (Session 1, slide 45), β comes only from the part of the decision that the controls did not predict, so it leans on contested meetings rather than giving a plain ATT."),
    bullet("<b>Standardisation</b> (Session 1, slide 49): fit returns on holds only, predict <i>Y</i>(0) for each hike, and average the differences."),
    bullet("<b>Inverse-odds weighting</b> (Session 1, slide 50): estimate the propensity <i>e</i>(<i>X</i>) = P(<i>T</i> = 1 | <i>X</i>) with a logit, and weight each hold by <i>e</i>/(1 − <i>e</i>) so that holds resemble hikes. The model uses the 3-month and 2-year spreads, the change in the 3-month yield, the last decision, inflation, unemployment and its change, the past 21-day return and VIX. We chose it using only pre-decision data, with no post-decision return in the script."),
    Spacer(1, 3),
    para("We report standardisation and weighting for all hikes and for <b>contested hikes</b>, those with a propensity below 0.9, where comparable holds exist. A within-band estimate, added after the plan was frozen, simply compares hikes and holds inside bands of similar propensity."),
    para(f"<b>Uncertainty.</b> We test two horizons, so each is tested at 2.5% (Bonferroni, Session 2), and main intervals are 97.5%. Regression uses HC3 standard errors, which stay cautious when a few meetings have high leverage. The other estimators resample whole calendar years, {n['n_bootstrap']:,} times, re-estimating everything each time, which keeps shocks within a year together. With a median of {n['median_gap_days']:.0f} trading days between decisions, the windows rarely overlap."),
    para("<b>A rule set in advance.</b> Before the final run we committed this rule to git. We claim an effect at a horizon only if: (1) the regression's 97.5% interval excludes zero; (2) both contested estimators share its sign and at least one interval excludes zero; "
         "(3) a fake-date placebo has an interval that includes zero and a size under half the estimate; and (4) a test on the next meeting's decision is not significant at 2.5%, with a size under half the estimate. "
         "<b>Disclosure:</b> an earlier test run looked at several windows and estimators, so the plan is not blind to the data. The horizons rest on design grounds: two days is the sharpest test, and 21 days is the longest window that usually closes before the next decision."),
]

# ----- 5. Descriptive analysis
band_rows = [["Chance of a hike", "Hikes", "Holds", "Gap, 2-day", "Gap, 21-day"]]
for _, row in strata.iterrows():
    band_rows.append([row["Chance of a hike"], int(row["Hikes"]), int(row["Holds"]),
                      "not comparable" if pd.isna(row["Gap, 2-day"]) else signed(row["Gap, 2-day"]),
                      "not comparable" if pd.isna(row["Gap, 21-day"]) else signed(row["Gap, 21-day"])])
balance = n["balance"]
story += [
    para("5. Descriptive analysis", H1),
    para(f"<b>Naive difference.</b> The raw gap is {num(n['main']['2-day|Naive gap'][0])} points at 2 days and {num(n['main']['21-day|Naive gap'][0])} at 21 days. Before reading anything into it, we ask how comparable the groups are. "
         f"Figure 3 shows they are not: {balance['n_raw_above_quarter']} of 18 variables differ by more than a quarter of a standard deviation, led by the 3-month yield relative to the target ({num(balance['raw_max'])} standard deviations). "
         f"Weighting contested hikes cuts the average gap from {num(balance['raw_mean'])} to {num(balance['contested_mean'])}, but {balance['n_contested_above_quarter']} variables stay above a quarter, so the outcome models also adjust for all 18."),
    figure("fig3_balance.png", "<b>Figure 3.</b> How far apart hike and hold meetings are, before and after weighting. The closer to zero, the more comparable.", width=WIDTH * 0.93),
    para(f"<b>Do comparable meetings exist?</b> This is the central tension of the project. Figure 4 shows that without market expectations hikes and holds overlap widely. With them, decisions become almost predictable the day before (AUC {num(n['auc_with'])}, where 1 is perfect), "
         f"and the effective number of comparison meetings falls from {n['ess_without']:.0f} to {n['ess_with']:.0f}. <b>The controls that make the comparison credible also destroy the overlap,</b> because the Fed rarely surprises markets. Table 4 shows the result plainly: {n['hikes_above_contested']} of {n['n_hike']} hikes fall in a band that has no holds at all. "
         f"For those hikes, any estimate is an extrapolation. That is why we report contested hikes separately."),
    figure("fig4_overlap.png", "<b>Figure 4.</b> Overlap between hike and hold meetings. The vertical axis is compressed above 10 meetings.", width=WIDTH * 0.93),
    table("Table 4. Comparing like with like: gaps inside bands of similar propensity (points)", band_rows, [0.3, 0.12, 0.12, 0.23, 0.23]),
    para(f"<b>Trends over time.</b> A clean decision effect would look flat before the decision and jump after it. Figure 5 looks different. On the decision day the gap is only {num(n['path_gap']['0'])} points; it then widens over the following weeks, to {num(n['path_gap']['21'])} at day 21. "
         f"The gap was also moving before the decision: over the two months before it, hold meetings rose about {num(n['path_gap']['-44'], 1)} points more than hike meetings. So part of the raw gap reflects different market regimes, or markets moving in anticipation. Section 7 tests whether the controls remove this."),
    figure("fig5_event_time.png", "<b>Figure 5.</b> Average S&P 500 path around each decision, and the gap between hike and hold meetings.", width=WIDTH * 0.93),
]

# ----- 6. Results
result_rows = [["Estimator", "Population", "2-day", "21-day"]]
populations = {"Naive gap": "All", "Regression": "Leans to contested", "Standardisation, all hikes": "All hikes", "Weighting, all hikes": "All hikes",
               "Standardisation, contested": "Contested hikes", "Weighting, contested": "Contested hikes", "Within bands, contested": "Contested hikes"}
names = {"Standardisation, all hikes": "Standardisation", "Weighting, all hikes": "Inverse-odds weighting", "Standardisation, contested": "Standardisation",
         "Weighting, contested": "Inverse-odds weighting", "Within bands, contested": "Within bands (added after freeze)", "Regression": "Regression (headline)"}
for method, population in populations.items():
    cells = []
    for horizon in ["2-day", "21-day"]:
        value, low, high = n["main"][f"{horizon}|{method}"]
        cells.append(f"{signed(value)} ({between(low, high)})")
    result_rows.append([names.get(method, method), population, *cells])
rule_rows = [["Condition for claiming an effect", "2-day", "21-day"]]
labels = {"1. Regression interval excludes zero": "1. Regression interval excludes zero",
          "2. Contested estimators agree in sign and one excludes zero": "2. Contested estimators agree in sign, and one excludes zero",
          "3. Fake date is clean": "3. Fake-date placebo is clean", "4. Lead test is clean": "4. Next meeting's decision shows no effect"}
for key, label in labels.items():
    rule_rows.append([label, "Pass" if n["rule"]["2-day"][key] else "Fail", "Pass" if n["rule"]["21-day"][key] else "Fail"])
rule_rows.append(["Causal effect claimed?", "No", "No"])
cuts = {r["Horizon"]: r for r in n["exploratory"] if r["Comparison"] == "Cut vs hold"}
influence_rows = [["Meeting", "Decision", "21-day return", "Regression without it"]]
for _, row in influence[influence["horizon"] == "21-day"].iterrows():
    influence_rows.append([f"{row['date'].day} {row['date'].strftime('%B %Y')}", row["decision"].capitalize(), f"{signed(row['return'], 1)}%", num(row["estimate_without"])])
story += [
    para("6. Results", H1),
    table("Table 5. Effect of a hike versus a hold on the S&P 500 return, in points, with 97.5% intervals", result_rows, [0.31, 0.19, 0.25, 0.25], bold_rows=(2,),
          note=f"{n['n_hike']} hikes and {n['n_hold']} holds ({n['n_hold'] - 1} at 21 days, because the last window has not closed). Naive gap and regression: HC3. Others: year-block bootstrap."),
    para(f"<b>First two days: no detectable effect.</b> All estimates are small, from {num(max(estimates_2))} to {num(min(estimates_2))}, and all intervals include zero. The regression gives {estimate('2-day|Regression')}, so its interval excludes a fall larger than about {num(abs(n['main']['2-day|Regression'][1]), 1)} points. "
         f"This fits anticipation: by the day before, a hike is mostly priced in."),
    para(f"<b>The following month: a lean, not a finding.</b> All seven estimates are negative, from {num(max(estimates_21))} to {num(min(estimates_21))}, and all intervals include zero. The regression gives {estimate('21-day|Regression')}, with <i>p</i> = {num(n['reg_p_y21'], 3)}, which misses our 2.5% level. "
         f"In plain terms: the data lean toward a hike lowering the next month's return by one to three points, but they cannot exclude zero."),
    para(f"<b>The size is less certain than the sign.</b> The largest estimates are the ones that extrapolate to hikes with no comparable holds. Estimates restricted to contested hikes are smaller, from {num(max(contested_21))} to {num(min(contested_21))}. One meeting also matters a great deal: "
         f"16 September 2008, the day after Lehman Brothers failed, was a hold followed by a {num(abs(top['top_return']), 1)}% fall. Its extreme yields tilt the regression, and without it the estimate is {num(without_top[0])} (Table 6). We keep it in the headline, as the plan requires, and we report the difference."),
    table("Table 6. The five meetings that most move the 21-day regression (headline: " + num(n["main"]["21-day|Regression"][0]) + ")", influence_rows, [0.3, 0.2, 0.25, 0.25]),
    para(f"<b>For whom?</b> The credible statement covers contested hikes, about {n['hikes_contested']} of {n['n_hike']}, where a hold was realistic. For the {n['hikes_above_contested']} hikes that looked close to certain the day before, the data cannot say what a hold would have done, because the Fed almost never held in those conditions."),
    figure("fig6_dynamic.png", "<b>Figure 6.</b> The gap by horizon (exploratory; Newey-West 95% intervals). It builds over weeks and shows no reversal within three months.", width=WIDTH * 0.9),
    table("Table 7. Applying the rule fixed before the final run", rule_rows, [0.62, 0.19, 0.19], bold_rows=(5,)),
    para(f"At 2 days there is little to detect. At 21 days both falsification tests pass, and the result fails for <b>lack of precision</b>, which is different from being refuted. The regression can reliably detect only effects of at least {num(n['mde_y1'], 1)} points at 2 days and {num(n['mde_y21'], 1)} at 21 days (80% power at the 2.5% level). "
         f"So a {COMPANY_THRESHOLD}-point effect, our illustrative threshold for acting, could exist and go undetected. The literature points the same way: Bernanke and Kuttner (2005) find about 1% for a surprise 25 basis point cut, and most hikes are largely expected, so the average effect may lie below what this sample can see."),
    para(f"<b>Cuts (exploratory).</b> Cuts versus holds give {num(cuts['21-day']['Naive'])} raw and {num(cuts['21-day']['Regression'])} adjusted at 21 days (standard errors {num(cuts['21-day']['Naive SE'])} and {num(cuts['21-day']['Regression SE'])}). Cuts are even more predictable than hikes (AUC {num(n['cut_auc'])}), so we draw no conclusion."),
]

# ----- 7. Checks and limits
test_rows = [["Test (controls measured before the window)", "2-day: raw", "2-day: adjusted", "21-day: raw", "21-day: adjusted"]]
for test, label in [("Fake date, one window earlier", "Fake date, one window earlier"), ("Fake date, two windows earlier", "Fake date, two windows earlier"),
                    ("Post minus pre", "Return after minus return before"), ("Lead test: next meeting's hike", "Next meeting's hike")]:
    row = [label]
    for horizon in ["2-day", "21-day"]:
        for column in ["Naive", "Adjusted"]:
            row.append(f"{signed(fake(horizon, test, column))} ({between(fake(horizon, test, column + ' low'), fake(horizon, test, column + ' high'))})")
    test_rows.append(row)
test_rows.append(["Fake calendars as large as the real gap", f"{n['replay_y1']['naive_p'] * 100:.0f}%", f"{n['replay_y1']['adjusted_p'] * 100:.0f}%", f"{n['replay_y21']['naive_p'] * 100:.0f}%", f"{n['replay_y21']['adjusted_p'] * 100:.1f}%"])
simulation_rows = [["Estimator", "Simple world: bias", "Simple world: RMSE", "Anticipation: bias", "Anticipation: RMSE"]]
for method, label in [("Naive gap", "Naive gap"), ("Regression", "Regression (headline)"), ("Standardisation, all hikes", "Standardisation, all hikes"),
                      ("Weighting, all hikes", "Weighting, all hikes"), ("Standardisation, contested", "Standardisation, contested"),
                      ("Weighting, contested", "Weighting, contested"), ("Within bands, contested", "Within bands, contested")]:
    simple, anticipation = sim[f"21-day|Simple|{method}"], sim[f"21-day|Anticipation|{method}"]
    simulation_rows.append([label, signed(simple[0]), num(simple[1]), signed(anticipation[0]), num(anticipation[1])])
assert sim["21-day|Simple|Regression"][1] == min(sim[f"21-day|Simple|{m}"][1] for m in populations), "The prose says regression has the lowest error."
assert sim["21-day|Anticipation|Regression"][1] == min(sim[f"21-day|Anticipation|{m}"][1] for m in populations), "The prose says regression has the lowest error."
story += [
    para("7. Checks and limits", H1),
    para(f"<b>Does the answer depend on our choices?</b> Figure 7 changes one choice at a time. At 2 days every interval includes zero. At 21 days the sign never changes, but the size does: {num(controls_high)} to {num(controls_low)} across control sets. No single hiking cycle drives the result ({num(cycle_high)} to {num(cycle_low)}), and comparing only within the same calendar year gives {num(same_year[0])}, so calendar regimes do not explain it away. "
         f"<b>Influence matters:</b> without the {top['top_date'][:4]} meeting the estimate is {num(without_top[0])}, without the five most influential meetings {num(without_five[0])}, and with the largest 2% of returns capped {num(capped[0])}. We added these three rows after the plan was frozen, because one check moved more than expected. "
         f"<b>Standard errors matter too:</b> clustering by year narrows the 95% interval to {between(clustered[1], clustered[2])}, and the year-block bootstrap gives a 97.5% interval of {between(*n['regression_bootstrap']['21-day'])}. Both exclude zero. We fixed HC3 in advance, and it is the cautious choice when leverage is this high, so we do not switch after seeing the result."),
    figure("fig7_checks.png", "<b>Figure 7.</b> The regression estimate with one choice changed at a time (95% intervals; note the different scales). Black: the headline.", width=WIDTH * 0.97),
    table("Table 8. Tests a real decision effect should pass (points, 97.5% intervals)", test_rows, [0.24, 0.19, 0.19, 0.19, 0.19],
          note="The last row slides the hike sequence along the calendar by every possible distance, which keeps cycles intact (Fisher's idea, Session 2), and gives the share of fake calendars with a gap at least as large."),
    para(f"<b>Falsification.</b> A decision cannot cause a return before it happens. The raw 21-day gap fails this standard in spirit: it is already {num(fake('21-day', 'Fake date, one window earlier', 'Naive'))} in the window before the decision. The adjusted comparison passes: {signed(fake('21-day', 'Fake date, one window earlier', 'Adjusted'))}, and the next meeting's hike shows {signed(n['lead_y21']['next'])}. "
         f"So the controls do remove the pre-decision gap, which supports the adjusted estimate over the raw one. Only {n['replay_y21']['adjusted_p'] * 100:.1f}% of fake calendars give an adjusted 21-day gap as large as the real one, which is the strongest evidence in favour of a real effect. At 2 days the fake-date gap of {signed(fake('2-day', 'Fake date, one window earlier', 'Adjusted'))} fits the known rise in stocks before FOMC meetings (Lucca and Moench, 2015). Measuring the change around the decision, the adjusted 21-day estimate is {num(fake('21-day', 'Post minus pre', 'Adjusted'))}, with a wide interval."),
    para(f"<b>Can the methods find a known truth?</b> We planted an effect of \u22121 point in simulated data with the real controls and overlap, in two worlds: a simple one, and one where a hold's return also rises with the expected chance of a hike. Table 9 shows that regression has the lowest error in both, although anticipation pulls it toward zero, while weighting contested hikes stays close to the truth but is noisier. This supports regression as the headline, with contested hikes reported beside it. "
         f"It also shows how low the power is: regression detects a true \u22121 point effect at 21 days in only {n['simulation_power']['21-day|Simple'] * 100:.0f}% of runs."),
    table("Table 9. Simulation with a known effect of \u22121 point, 21-day horizon (500 runs per world)", simulation_rows, [0.34, 0.165, 0.165, 0.165, 0.165]),
    para(f"<b>How strong would a hidden confounder have to be?</b> Using the omitted-variable logic of Session 1 (Cinelli and Hazlett, 2020), a hidden factor would need to explain {sens['rv_to_zero'] * 100:.0f}% of the leftover variation in both the decision and the 21-day return to bring the estimate to zero. Our strongest observed controls explain at most {sens['max_outcome'] * 100:.0f}% of the return and {sens['max_treatment'] * 100:.0f}% of the decision. So a hidden factor would have to be about three times as strong to remove the estimate entirely, although one explaining about {sens['rv_to_insignificant'] * 100:.0f}% of each would be enough to remove statistical significance, even with the classical standard errors this calculation uses."),
    para("<b>Limits.</b>"),
    bullet("<b>Markets anticipate.</b> About half of all hikes have no comparable hold, so any estimate for them is an extrapolation."),
    bullet("<b>We measure the decision, not the whole tightening.</b> Returns start the day before, so what markets priced earlier in a cycle is not counted. Measuring surprises directly needs fed funds futures, which we do not have."),
    bullet("<b>Hidden confounding remains possible.</b> The Fed may know things markets do not (Nakamura and Steinsson, 2018; Jarociński and Karadi, 2020), and other news arrives inside a 21-day window."),
    bullet(f"<b>Few independent episodes.</b> There are {n['n_hike']} hikes but only seven hiking cycles, and one meeting moves the headline by a full point."),
    bullet("<b>Measurement.</b> Macro data use today's revisions, returns exclude dividends, and a hold is not one treatment. The results describe this US regime since 1994."),
]

# ----- 8. Conclusion
story += [
    para("8. Conclusion", H1),
    para(f"<b>Answer.</b> We do not find that the average Fed hike, by itself, moves the S&P 500 in the first two days ({estimate_sentence('2-day|Regression')}). Over the following month, the evidence leans toward a lower return of roughly one to three points, but it cannot exclude zero (the regression gives {estimate_sentence('21-day|Regression')}), and one crisis meeting moves that estimate by a full point. "
         f"By our pre-set rule we claim no causal effect. The safest statement is Lab 1's: after adjustment, hikes were associated with lower returns over the next month among comparable meetings."),
    para(f"<b>Recommendation.</b> Do not treat an announced hike as a signal to trade or to change plans on the day. The 21-day interval includes both zero and our illustrative {COMPANY_THRESHOLD}-point threshold, so the data do not justify a standing rule to hedge on every hike. For planning, treat a lower return of a few points in the month after a hike as a stress scenario, not a forecast. "
         "And watch how far a decision differs from what markets expected, because that is where the literature finds the effect, and this design cannot measure it directly. A stronger study would use fed funds futures surprises around each announcement."),
    para("References", H1),
]
for reference in [
    "Angrist, J., Jordà, Ò. and Kuersteiner, G. (2018). Semiparametric estimates of monetary policy effects: string theory revisited. <i>Journal of Business &amp; Economic Statistics</i> 36(3).",
    "Bernanke, B. and Kuttner, K. (2005). What explains the stock market's reaction to Federal Reserve policy? <i>Journal of Finance</i> 60(3).",
    "Cinelli, C. and Hazlett, C. (2020). Making sense of sensitivity: extending omitted variable bias. <i>Journal of the Royal Statistical Society B</i> 82(1).",
    "Diallo, A. (2026). <i>Causal Inference</i>, course sessions and labs, Albert School.",
    "Holland, P. (1986). Statistics and causal inference. <i>Journal of the American Statistical Association</i> 81(396).",
    "Jarociński, M. and Karadi, P. (2020). Deconstructing monetary policy surprises: the role of information shocks. <i>American Economic Journal: Macroeconomics</i> 12(2).",
    "Lucca, D. and Moench, E. (2015). The pre-FOMC announcement drift. <i>Journal of Finance</i> 70(1).",
    "Miranda-Agrippino, S. and Rey, H. (2020). U.S. monetary policy and the global financial cycle. <i>Review of Economic Studies</i> 87(6).",
    "Nakamura, E. and Steinsson, J. (2018). High-frequency identification of monetary non-neutrality: the information effect. <i>Quarterly Journal of Economics</i> 133(3).",
    "Poole, W. and Rasche, R. (2003). The impact of changes in FOMC disclosure practices on the transparency of monetary policy. <i>Federal Reserve Bank of St. Louis Review</i> 85(1).",
]:
    story.append(para(reference, REF))

document = BaseDocTemplate(
    str(OUTPUT), pagesize=A4, leftMargin=2.1 * cm, rightMargin=2.1 * cm, topMargin=1.9 * cm, bottomMargin=1.9 * cm,
    title="Does a Fed Rate Hike Move the S&P 500?", author=AUTHOR, subject="M2 Causal Inference final project, Albert School",
)
document.addPageTemplates([PageTemplate(id="page", frames=[Frame(document.leftMargin, document.bottomMargin, document.width, document.height, id="body", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer)])
document.build(story)
print(f"Wrote {OUTPUT.relative_to(ROOT)}: {document.page} pages")
