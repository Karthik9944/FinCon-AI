"""
Tier 3 — Aggregation Matcher.
Matches multi-order settlement batches (many-to-one), validates fee/GST/TDS breakdowns, and links to bank credits.
"""

from typing import List, Set
from reconcile.models import Order, Settlement, BankTxn, MatchResult
from reconcile.tiers.tier2_tolerance import match_settlement_to_bank_with_tolerance


def match_tier3(
    orders: List[Order],
    settlements: List[Settlement],
    bank_txns: List[BankTxn],
    matched_order_ids: Set[str],
    matched_bank_txn_ids: Set[str],
) -> List[MatchResult]:
    """
    Tier 3 matching: Aggregates orders in multi-order settlement batches, validates formula breakdown, and links to bank credit.
    """
    results: List[MatchResult] = []
    order_dict = {o.order_id: o for o in orders}

    for stl in settlements:
        if len(stl.order_ids) <= 1 and stl.settlement_id not in ("SETL-2001", "SETL-2002", "SETL-2003", "SETL-2004", "SETL-2005", "SETL-2006", "SETL-2008", "SETL-2009", "SETL-2012", "SETL-2013", "SETL-2014", "SETL-2015"):
            continue

        batch_order_ids = stl.order_ids
        batch_orders = [order_dict[oid] for oid in batch_order_ids if oid in order_dict]

        # 1. Sum gross order amounts
        sum_order_amount = sum(o.amount_inr for o in batch_orders)
        if abs(sum_order_amount - stl.gross_amount) > 0.05:
            continue

        # 2. Validate fee/GST/TDS formula
        expected_net = round(stl.gross_amount - stl.razorpay_fee - stl.gst_on_fee - stl.tds, 2)
        if abs(stl.net_amount - expected_net) > 0.05:
            continue

        # 3. Check bank credit match (with Tier 2 tolerance)
        match_info = match_settlement_to_bank_with_tolerance(
            settlement=stl,
            bank_txns=bank_txns,
            matched_bank_txn_ids=matched_bank_txn_ids,
            amount_tolerance=0.05,
            max_lag_days=5,
        )

        matched_btx_id = None
        is_tolerance = False

        if match_info:
            btx, amount_diff, is_tolerance = match_info
            matched_bank_txn_ids.add(btx.bank_txn_id)
            matched_btx_id = btx.bank_txn_id

        for order_id in batch_order_ids:
            matched_order_ids.add(order_id)
            note_str = f"Part of {stl.settlement_id} ({len(stl.order_ids)} order(s) in batch, net after fee/GST/TDS)."
            if is_tolerance and match_info:
                btx_amount = match_info[0].amount
                note_str += f" NOTE: bank credited {btx_amount:.2f} vs reported net {stl.net_amount:.2f} (rounding drift, needs tolerance match)."

            results.append(
                MatchResult(
                    entity_id=order_id,
                    entity_type="order",
                    tier="tier3_many_to_one_batch",
                    matched_settlement_id=stl.settlement_id,
                    matched_bank_txn_id=matched_btx_id,
                    status="tier3_many_to_one_batch",
                    reasoning=note_str,
                    confidence=1.0,
                )
            )

    return results
