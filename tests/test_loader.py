"""
Unit tests for data ingestion loader.
"""

import os
import unittest
from reconcile.loader import load_orders, load_settlements, load_bank_transactions, load_ground_truth

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class TestLoader(unittest.TestCase):
    def test_load_orders(self):
        orders = load_orders(DATA_DIR)
        self.assertGreater(len(orders), 50)
        first = orders[0]
        self.assertTrue(first.order_id.startswith("ORD-"))
        self.assertGreater(first.amount_inr, 0)

    def test_load_settlements(self):
        settlements = load_settlements(DATA_DIR)
        self.assertGreater(len(settlements), 10)
        first = settlements[0]
        self.assertTrue(first.settlement_id.startswith("SETL-"))
        self.assertTrue(first.utr.startswith("UTR"))
        self.assertGreaterEqual(len(first.order_ids), 1)
        expected_net = round(first.gross_amount - first.razorpay_fee - first.gst_on_fee - first.tds, 2)
        self.assertLessEqual(abs(first.net_amount - expected_net), 0.05)

    def test_load_bank_transactions(self):
        txns = load_bank_transactions(DATA_DIR)
        self.assertGreaterEqual(len(txns), 20)
        first = txns[0]
        self.assertTrue(first.bank_txn_id.startswith("BTX-"))
        self.assertIn(first.txn_type, ("credit", "debit"))

    def test_load_ground_truth(self):
        gt = load_ground_truth(DATA_DIR)
        self.assertGreaterEqual(len(gt), 70)
        self.assertIn("expected_bucket", gt[0])


if __name__ == "__main__":
    unittest.main()

