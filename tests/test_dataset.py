import unittest
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "notebooks" / "fed_sp500_daily.csv"
CONTROLS = [
    "fed_target", "yield_3m", "yield_1y", "yield_2y", "yield_10y", "vix", "credit_spread",
    "inflation_yoy", "unemployment", "unemp_change_3m", "ind_prod_yoy",
]


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(CSV, parse_dates=["date"]).set_index("date")
        cls.decisions = cls.data.dropna(subset=["fomc_decision"])

    def test_dates_are_sorted_and_unique(self):
        self.assertTrue(self.data.index.is_monotonic_increasing)
        self.assertTrue(self.data.index.is_unique)

    def test_decision_counts_match_official_record(self):
        counts = self.decisions["fomc_decision"].value_counts()
        self.assertEqual(counts["hike"], 52)
        self.assertEqual(counts["hold"], 179)
        self.assertEqual(counts["cut"], 40)

    def test_known_decisions(self):
        for day, decision in [
            ("1994-02-04", "hike"), ("2004-06-30", "hike"), ("2022-03-16", "hike"),
            ("2001-09-17", "cut"), ("2008-12-16", "cut"), ("2020-03-16", "cut"),
            ("2019-01-30", "hold"), ("2010-08-10", "hold"),
        ]:
            self.assertEqual(self.data.loc[day, "fomc_decision"], decision, day)

    def test_target_moves_only_around_decisions(self):
        target = self.data["fed_target"]
        moves = target.index[target.diff().abs() > 1e-9]
        for move in moves[moves >= "1994-02-01"]:
            nearest = abs((self.decisions.index - move).days).min()
            self.assertLessEqual(nearest, 4, move)

    def test_controls_are_complete_at_every_decision(self):
        self.assertEqual(self.decisions[CONTROLS].isna().sum().sum(), 0)

    def test_macro_values_wait_for_publication(self):
        # A month is not treated as known until the 20th of the next month.
        inflation = self.data["inflation_yoy"]
        self.assertEqual(inflation.loc["2022-03-18"], inflation.loc["2022-02-22"])
        self.assertNotEqual(inflation.loc["2022-03-18"], inflation.loc["2022-03-21"])


if __name__ == "__main__":
    unittest.main()
