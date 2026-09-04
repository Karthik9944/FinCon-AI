"""
Unit tests for Tier 2 tolerance matching.
"""

import unittest
from reconcile.models import Settlement, BankTxn
from reconcile.tiers.tier2_tolerance import match_settlement_to_bank_with_tolerance


class TestTier2(unittest.TestCase):
    def test_tolerance_rounding_and_lag(self):
        # Settlement net is 30708.16, bank credited 30708.15 (0.01 drift)
        stl = Settlement("SETL-2006", "UTR885884RZP", "2026-08-10", ["ORD-1011", "ORD-1018", "ORD-1028"], 31482.63, 629.65, 113.34, 31.48, 30708.16)
        btx = BankTxn("BTX-5005", "2026-08-10", 30708.15, "credit", "UPI-UTR885884RZP-RAZORPAYX")

        matched_bank = set()
        match_info = match_settlement_to_bank_with_tolerance(stl, [btx], matched_bank, amount_tolerance=0.05, max_lag_days=5)

        self.assertIsNotNone(match_info)
        matched_btx, diff, is_tol = match_info
        self.assertEqual(matched_btx.bank_txn_id, "BTX-5005")
        self.assertAlmostEqual(diff, 0.01, places=3)
        self.assertTrue(is_tol)


if __name__ == "__main__":
    unittest.main()
