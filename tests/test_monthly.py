import unittest

import pandas as pd

from casual_inference_finance.monthly import prepare_monthly_data


class MonthlyAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.prices = pd.Series(
            [100., 105., 110., 121., 133.1],
            index=pd.to_datetime(['2020-01-31', '2020-02-14', '2020-02-28',
                                      '2020-03-31', '2020-04-30']),
        )
        self.fed = pd.DataFrame({
            'observation_date': ['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01'],
            'FEDFUNDS': [1., 1.25, 1.25, 1.],
        })

    def test_month_end_units_and_forward_outcome(self):
        result = prepare_monthly_data(self.prices, self.fed)
        self.assertEqual(result.loc['2020-02', 'sp500_close'], 110.)
        self.assertAlmostEqual(result.loc['2020-02', 'sp500_return'], .1)
        self.assertAlmostEqual(result.loc['2020-02', 'next_month_return'], .1)
        self.assertEqual(result.loc['2020-02', 'rate_change_pp'], .25)
        self.assertEqual(result.loc['2020-02', 'rate_direction'], 'increase')
        self.assertTrue(pd.isna(result.iloc[-1]['next_month_return']))

    def test_missing_price_month_does_not_bridge_gap(self):
        result = prepare_monthly_data(self.prices.drop(pd.Timestamp('2020-03-31')), self.fed)
        self.assertTrue(pd.isna(result.loc['2020-04', 'sp500_return']))
        self.assertTrue(pd.isna(result.loc['2020-02', 'next_month_return']))

    def test_missing_rate_is_not_filled(self):
        self.fed.loc[1, 'FEDFUNDS'] = float('nan')
        result = prepare_monthly_data(self.prices, self.fed)
        self.assertTrue(pd.isna(result.loc['2020-03', 'rate_change_pp']))
        self.assertTrue(pd.isna(result.loc['2020-03', 'rate_direction']))

    def test_duplicate_fed_month_rejected(self):
        with self.assertRaises(ValueError):
            prepare_monthly_data(self.prices, pd.concat([self.fed, self.fed.iloc[:1]]))


if __name__ == '__main__':
    unittest.main()
