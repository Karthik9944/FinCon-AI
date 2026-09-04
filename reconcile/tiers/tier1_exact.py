"""
Tier 1 — Exact Matcher.
Matches single-order settlements directly linked to bank credits via UTR and exact amounts.
"""

from typing import List, Set
from reconcile.models import Order, Settlement, BankTxn, MatchResult


def match_tier1(
    orders: List[Order],
    settlements: List[Settlement],
    bank_txns: List[BankTxn],
    matched_order_ids: Set[str],
    matched_bank_txn_ids: Set[str],
) -> List[MatchResult]:
    """
    Tier 1 matching: Matches single-order settlements with direct UTR match in bank narration and exact net amount.
    """
    results: List[MatchResult] = []
    order_dict = {o.order_id: o for o in orders}

    for stl in settlements:
        if len(stl.order_ids) != 1:
            continue  # Tier 1 handles single-order batches

        order_id = stl.order_ids[0]
        if order_id in matched_order_ids or order_id not in order_dict:
            continue

        # Find matching bank transaction credit
        for btx in bank_txns:
            if btx.bank_txn_id in matched_bank_txn_ids or btx.txn_type != "credit":
                continue

            if stl.utr in btx.narration:
                if abs(btx.amount - stl.net_amount) < 0.01:
                    matched_order_ids.add(order_id)
                    matched_bank_txn_ids.add(btx.bank_txn_id)

                    results.append(
                        MatchResult(
                            entity_id=order_id,
                            entity_type="order",
                            tier="tier1_exact_single",
                            matched_settlement_id=stl.settlement_id,
                            matched_bank_txn_id=btx.bank_txn_id,
                            status="tier1_exact_single",
                            reasoning=f"Part of {stl.settlement_id} (1 order(s) in batch, net after fee/GST/TDS).",
                            confidence=1.0,
                        )
                    )
                    break

    return results
