"""
Unit tests for Tier 4 LLM residual agent guardrails and failure recovery.
"""

import unittest
from reconcile.models import Order, BankTxn
from reconcile.tiers.tier4_llm_agent import resolve_llm_residuals


class TestTier4Guardrails(unittest.TestCase):
    def test_guardrail_accepts_high_confidence(self):
        unmatched_orders = [
            Order("ORD-1013", "2026-08-20", "Meera", "POS", 11911.36, "Card", "partial_refund")
        ]
        unmatched_bank = [
            BankTxn("BTX-5016", "2026-09-03", 4873.68, "debit", "REFUND-ORD-1013-PARTIAL")
        ]

        results, audit_logs = resolve_llm_residuals(unmatched_orders, unmatched_bank, confidence_threshold=0.85)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_id, "ORD-1013")
        self.assertEqual(results[0].status, "partial_refund")
        self.assertEqual(audit_logs[0]["outcome"], "ACCEPTED")

    def test_guardrail_rejects_low_confidence(self):
        unmatched_orders = [
            Order("ORD-1048", "2026-08-11", "Karan", "Fee", 1481.83, "Card", "created")
        ]
        unmatched_bank = [
            BankTxn("BTX-5020", "2026-08-16", 118.0, "debit", "AMB CHARGES-AUG")
        ]

        results, audit_logs = resolve_llm_residuals(unmatched_orders, unmatched_bank, confidence_threshold=0.85)

        self.assertEqual(len(results), 0)  # Low confidence proposals are NOT promoted to matched
        self.assertEqual(len(audit_logs), 1)
        self.assertEqual(audit_logs[0]["outcome"], "REJECTED_BY_GUARDRAIL")
        self.assertIn("below safety threshold", audit_logs[0]["rejection_reason"])


if __name__ == "__main__":
    unittest.main()
