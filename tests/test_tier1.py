"""
Unit tests for Tier 1 exact matching.
"""

import unittest
from reconcile.models import Order, Settlement, BankTxn
from reconcile.tiers.tier1_exact import match_tier1


class TestTier1(unittest.TestCase):
    def test_tier1_exact_single_match(self):
        orders = [
            Order("ORD-1033", "2026-08-01", "Customer A", "Product A", 1605.67, "UPI", "created")
        ]
        settlements = [
            Settlement("SETL-2007", "UTR348237RZP", "2026-08-10", ["ORD-1033"], 1605.67, 32.11, 5.78, 1.61, 1566.17)
        ]
        bank_txns = [
            BankTxn("BTX-5006", "2026-08-10", 1566.17, "credit", "NEFT-RAZORP-UTR348237RZP")
        ]

        matched_orders = set()
        matched_bank = set()
        results = match_tier1(orders, settlements, bank_txns, matched_orders, matched_bank)

        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.entity_id, "ORD-1033")
        self.assertEqual(res.tier, "tier1_exact_single")
        self.assertEqual(res.status, "tier1_exact_single")
        self.assertIn("ORD-1033", matched_orders)
        self.assertIn("BTX-5006", matched_bank)


if __name__ == "__main__":
    unittest.main()
