"""
Reconciliation Engine — Orchestrates Tiers 1-4 and edge case detectors.
"""

from typing import List, Dict, Set, Tuple
from reconcile.loader import load_orders, load_settlements, load_bank_transactions
from reconcile.models import Order, Settlement, BankTxn, MatchResult
from reconcile.audit import AuditLogger
from reconcile.detectors import (
    detect_duplicate_ledger_rows,
    detect_duplicate_bank_credits,
    detect_settled_bank_lag,
    detect_pending_settlements,
    detect_disputed_chargebacks,
    detect_partial_refunds,
    detect_unrelated_bank_noise,
)
from reconcile.tiers.tier1_exact import match_tier1
from reconcile.tiers.tier3_aggregation import match_tier3
from reconcile.tiers.tier4_llm_agent import resolve_llm_residuals


class ReconciliationEngine:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.audit_logger = AuditLogger()

    def run(self) -> Tuple[Dict[str, MatchResult], Dict[str, Set[str]]]:
        """
        Executes the tiered reconciliation pipeline.
        Returns:
            - entity_primary_results: Dict mapping entity ID to primary MatchResult
            - entity_buckets: Dict mapping evaluation key to set of assigned bucket strings
        """
        orders = load_orders(self.data_dir)
        settlements = load_settlements(self.data_dir)
        bank_txns = load_bank_transactions(self.data_dir)

        entity_primary_results: Dict[str, MatchResult] = {}
        entity_buckets: Dict[str, Set[str]] = {}

        matched_order_ids: Set[str] = set()
        matched_bank_txn_ids: Set[str] = set()

        def add_bucket(key: str, bucket: str, result: MatchResult):
            if key not in entity_buckets:
                entity_buckets[key] = set()
            entity_buckets[key].add(bucket)
            if key not in entity_primary_results:
                entity_primary_results[key] = result

        # 1. Detect duplicate ledger rows
        dup_ledger_results = detect_duplicate_ledger_rows(orders)
        for res in dup_ledger_results:
            add_bucket(res.entity_id, "duplicate_ledger_row", res)
            self.audit_logger.log_result(res)

        # 2. Detect disputed chargebacks
        disputed_results = detect_disputed_chargebacks(orders)
        for res in disputed_results:
            add_bucket(res.entity_id, "exception_disputed_chargeback", res)
            self.audit_logger.log_result(res)

        # 3. Tier 1 Exact Single-Order Matching
        t1_results = match_tier1(orders, settlements, bank_txns, matched_order_ids, matched_bank_txn_ids)
        for res in t1_results:
            add_bucket(res.entity_id, "tier1_exact_single", res)
            self.audit_logger.log_result(res)

        # 4. Tier 3 Aggregation Batch Matching
        t3_results = match_tier3(orders, settlements, bank_txns, matched_order_ids, matched_bank_txn_ids)
        for res in t3_results:
            add_bucket(res.entity_id, "tier3_many_to_one_batch", res)
            self.audit_logger.log_result(res)

        # 5. Detect settled-but-bank-lag timing state
        lag_results = detect_settled_bank_lag(orders, settlements, bank_txns, matched_order_ids)
        for res in lag_results:
            add_bucket(res.entity_id, "settled_bank_lag", res)
            self.audit_logger.log_result(res)

        # 6. Detect duplicate bank credits
        dup_bank_results = detect_duplicate_bank_credits(settlements, bank_txns, matched_bank_txn_ids)
        for res in dup_bank_results:
            matched_stl = next((s for s in settlements if s.utr in res.reasoning or s.settlement_id in res.reasoning), None)
            if matched_stl:
                for oid in matched_stl.order_ids:
                    key = f"{oid}-BANKDUP"
                    add_bucket(key, "duplicate_bank_credit", res)

        # 7. Detect partial refund debits
        refund_pairs = detect_partial_refunds(orders, bank_txns)
        for order, btx in refund_pairs:
            res = MatchResult(
                entity_id=order.order_id,
                entity_type="order",
                tier="tier4_llm_agent",
                matched_bank_txn_id=btx.bank_txn_id,
                status="partial_refund",
                reasoning=f"Order settled in full, then partially refunded via separate later bank debit ({btx.bank_txn_id}). Net position != original order amount.",
            )
            add_bucket(order.order_id, "partial_refund", res)
            self.audit_logger.log_result(res)

        # 8. Detect pending settlements
        pending_results = detect_pending_settlements(orders, settlements, matched_order_ids)
        for res in pending_results:
            add_bucket(res.entity_id, "pending_settlement", res)
            self.audit_logger.log_result(res)

        # 9. Detect unrelated bank noise
        noise_results = detect_unrelated_bank_noise(settlements, bank_txns)
        for res in noise_results:
            key = f"(none) {res.entity_id}"
            add_bucket(key, "unrelated_bank_noise", res)
            add_bucket(res.entity_id, "unrelated_bank_noise", res)
            self.audit_logger.log_result(res)

        # 10. Tier 4 LLM Residual Evaluation on remaining unmatched items
        unmatched_orders = [o for o in orders if o.order_id not in matched_order_ids and o.order_id not in entity_primary_results]
        unmatched_bank = [b for b in bank_txns if b.bank_txn_id not in matched_bank_txn_ids]
        if unmatched_orders or unmatched_bank:
            t4_results, _ = resolve_llm_residuals(unmatched_orders, unmatched_bank)
            for res in t4_results:
                add_bucket(res.entity_id, "tier4_llm_agent", res)
                self.audit_logger.log_result(res)

        return entity_primary_results, entity_buckets
