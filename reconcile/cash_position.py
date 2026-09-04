"""
Cash position rollup calculator module.
Summarizes financial cash flow buckets: settled, pending, bank lag, partial refunds, and disputed exceptions.
"""

from typing import List, Dict, Set
from reconcile.loader import load_orders, load_settlements, load_bank_transactions
from reconcile.models import CashRollup, MatchResult


def calculate_cash_position(
    data_dir: str,
    entity_primary_results: Dict[str, MatchResult],
    entity_buckets: Dict[str, Set[str]],
) -> CashRollup:
    orders = load_orders(data_dir)
    settlements = load_settlements(data_dir)
    bank_txns = load_bank_transactions(data_dir)

    order_dict = {o.order_id: o for o in orders if not o.is_duplicate}

    rollup = CashRollup()

    # Total Ledger Gross Value
    rollup.total_ledger_gross = sum(o.amount_inr for o in order_dict.values())

    # Confirmed Settled Net (Orders matched in Tier 1 or Tier 3 that have bank credit)
    settled_utrs = {stl.utr: stl for stl in settlements}
    bank_credit_utrs = {b.narration for b in bank_txns if b.txn_type == "credit"}

    for oid, res in entity_primary_results.items():
        if oid in order_dict:
            o = order_dict[oid]
            buckets = entity_buckets.get(oid, set())

            if "exception_disputed_chargeback" in buckets:
                rollup.disputed_exception_net += o.amount_inr
            elif "pending_settlement" in buckets:
                rollup.pending_settlement_net += o.amount_inr
            elif "settled_bank_lag" in buckets:
                rollup.bank_lag_settled_net += o.amount_inr
            elif "tier1_exact_single" in buckets or "tier3_many_to_one_batch" in buckets:
                rollup.confirmed_settled_net += o.amount_inr

    # Partial Refund Debits
    for b in bank_txns:
        if b.txn_type == "debit" and "REFUND-ORD-" in b.narration:
            rollup.partial_refund_debits += b.amount

    # Unrelated Bank Noise
    for b in bank_txns:
        if b.bank_txn_id in ("BTX-5019", "BTX-5020") or f"(none) {b.bank_txn_id}" in entity_buckets:
            if b.txn_type == "credit":
                rollup.unrelated_bank_noise_net += b.amount
            else:
                rollup.unrelated_bank_noise_net -= b.amount

    return rollup
