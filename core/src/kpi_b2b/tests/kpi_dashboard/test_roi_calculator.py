import unittest

from kpi_b2b.kpi_dashboard.domain.services.roi_calculator import RoiCalculator


class TestRoiCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = RoiCalculator()

    def test_calculate_payback_period_success(self):
        res = self.calculator.calculate_payback_period(
            turnkey_quote_cost=300000000.0,  # 3억원
            baseline_oee=0.70,
            improved_oee=0.84,  # OEE 20% 향상
            monthly_base_revenue=100000000.0,  # 월 매출 1억원
        )

        self.assertEqual(res.payback_period_months, 15.0)  # 15개월 회수
        self.assertGreater(res.roi_percentage, 0.0)


if __name__ == "__main__":
    unittest.main()
