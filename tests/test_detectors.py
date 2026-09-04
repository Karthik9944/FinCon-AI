"""
Unit tests for edge case detectors.
"""

import unittest
from reconcile.models import Order, Settlement, BankTxn
from reconcile.detectors import (
    detect_duplicate_ledger_rows,
    detect_duplicate_bank_credits,
    detect_settled_bank_lag,
    detect_pending_settlements,
    detect_disputed_chargebacks,
    detect_unrelated_bank_noise,
)


class TestDetectors(unittest.TestCase):
    def test_duplicate_ledger_row(self):
        orders = [
            Order("ORD-1035", "2026-08-08", "Customer A", "Prod", 100.0, "UPI", "created"),
            Order("ORD-1035-DUP", "2026-08-08", "Customer A", "Prod", 100.0, "UPI", "created"),
        ]
        res = detect_duplicate_ledger_rows(orders)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].entity_id, "ORD-1035-DUP")
        self.assertEqual(res[0].status, "duplicate_ledger_row")

    def test_duplicate_bank_credit(self):
        settlements = [
            Settlement("SETL-2008", "UTR270395RZP", "2026-08-12", ["ORD-1035"], 100.0, 2.0, 0.36, 1.0, 96.64)
        ]
        bank_txns = [
            BankTxn("BTX-5007", "2026-08-12", 96.64, "credit", "IMPS/UTR270395RZP/RZRPY"),
            BankTxn("BTX-5008", "2026-08-12", 96.64, "credit", "IMPS/UTR270395RZP/RZRPY"),
        ]
        matched_bank = set()
        res = detect_duplicate_bank_credits(settlements, bank_txns, matched_bank)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].entity_id, "BTX-5008")
        self.assertEqual(res[0].status, "duplicate_bank_credit")

    def test_disputed_chargeback(self):
        orders = [
            Order("ORD-1047", "2026-08-05", "Customer B", "Prod", 500.0, "UPI", "disputed")
        ]
        res = detect_disputed_chargebacks(orders)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].status, "exception_disputed_chargeback")

    def test_unrelated_bank_noise(self):
        settlements = [
            Settlement("SETL-2001", "UTR320281RZP", "2026-08-04", ["ORD-1001"], 100.0, 2.0, 0.36, 1.0, 96.64)
        ]
        bank_txns = [
            BankTxn("BTX-5019", "2026-08-11", 212.5, "credit", "SAVINGS INT CREDIT Q2")
        ]
        res = detect_unrelated_bank_noise(settlements, bank_txns)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].status, "unrelated_bank_noise")


if __name__ == "__main__":
    unittest.main()
