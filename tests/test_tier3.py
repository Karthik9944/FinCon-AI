"""
Unit tests for Tier 3 aggregation matching.
"""

import unittest
from reconcile.models import Order, Settlement, BankTxn
from reconcile.tiers.tier3_aggregation import match_tier3


class TestTier3(unittest.TestCase):
    def test_tier3_aggregation_batch(self):
        orders = [
            Order("ORD-1054", "2026-08-01", "Customer A", "Product A", 8722.05, "Card", "created"),
            Order("ORD-1003", "2026-08-02", "Customer B", "Product B", 987.84, "UPI", "created"),
        ]
        # Gross = 8722.05 + 987.84 = 9709.89
        settlements = [
            Settlement("SETL-2001", "UTR320281RZP", "2026-08-04", ["ORD-1054", "ORD-1003"], 9709.89, 194.2, 34.96, 9.71, 9471.02)
        ]
        bank_txns = [
            BankTxn("BTX-5001", "2026-08-04", 9471.02, "credit", "UPI-UTR320281RZP-RAZORPAYX")
        ]

        matched_orders = set()
        matched_bank = set()
        results = match_tier3(orders, settlements, bank_txns, matched_orders, matched_bank)

        self.assertEqual(len(results), 2)
        self.assertIn("ORD-1054", matched_orders)
        self.assertIn("ORD-1003", matched_orders)
        self.assertIn("BTX-5001", matched_bank)
        for r in results:
            self.assertEqual(r.tier, "tier3_many_to_one_batch")
            self.assertEqual(r.status, "tier3_many_to_one_batch")


if __name__ == "__main__":
    unittest.main()
