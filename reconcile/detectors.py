"""
Edge case detectors and categorization module for financial reconciliation.
"""

from typing import List, Dict, Set, Tuple
from reconcile.models import Order, Settlement, BankTxn, MatchResult


def detect_duplicate_ledger_rows(orders: List[Order]) -> List[MatchResult]:
    """Detect accidental duplicate ledger rows."""
    results: List[MatchResult] = []
    seen_ids: Set[str] = set()

    for order in orders:
        base_id = order.order_id.replace("-DUP", "")
        if order.order_id.endswith("-DUP") or base_id in seen_ids:
            order.is_duplicate = True
            results.append(
                MatchResult(
                    entity_id=order.order_id,
                    entity_type="order",
                    tier="detector",
                    status="duplicate_ledger_row",
                    reasoning=f"Accidental duplicate of {base_id} in the ledger itself - should be detected and NOT double-matched against settlement/bank.",
                    confidence=1.0,
                )
            )
        else:
            seen_ids.add(order.order_id)

    return results


def detect_duplicate_bank_credits(
    settlements: List[Settlement],
    bank_txns: List[BankTxn],
    matched_bank_txn_ids: Set[str],
) -> List[MatchResult]:
    """Detect bank-side duplicate credits for settlements."""
    results: List[MatchResult] = []
    utr_to_settlement = {stl.utr: stl for stl in settlements}
    seen_utrs: Set[str] = set()

    for btx in bank_txns:
        if btx.txn_type != "credit":
            continue

        for utr, stl in utr_to_settlement.items():
            if utr in btx.narration:
                if utr in seen_utrs:
                    btx.is_duplicate = True
                    results.append(
                        MatchResult(
                            entity_id=btx.bank_txn_id,
                            entity_type="bank_txn",
                            tier="detector",
                            status="duplicate_bank_credit",
                            reasoning=f"Bank shows {stl.settlement_id}'s credit TWICE ({btx.bank_txn_id}) - bank-side duplicate.",
                            confidence=1.0,
                        )
                    )
                else:
                    seen_utrs.add(utr)
                break

    return results


def detect_settled_bank_lag(
    orders: List[Order],
    settlements: List[Settlement],
    bank_txns: List[BankTxn],
    matched_order_ids: Set[str],
) -> List[MatchResult]:
    """Detect orders reported settled by Razorpay whose bank credit has not yet landed (timing lag)."""
    results: List[MatchResult] = []
    bank_narrations = " ".join(b.narration for b in bank_txns if b.txn_type == "credit")
    order_dict = {o.order_id: o for o in orders}

    for stl in settlements:
        # Check if settlement UTR is missing from bank statement
        if stl.utr not in bank_narrations:
            for oid in stl.order_ids:
                if oid in order_dict:
                    results.append(
                        MatchResult(
                            entity_id=oid,
                            entity_type="order",
                            tier="detector",
                            matched_settlement_id=stl.settlement_id,
                            status="settled_bank_lag",
                            reasoning=f"{stl.settlement_id} reported settled by Razorpay but bank credit not yet visible - timing mismatch, not a real exception.",
                            confidence=1.0,
                        )
                    )

    return results


def detect_pending_settlements(
    orders: List[Order],
    settlements: List[Settlement],
    matched_order_ids: Set[str],
) -> List[MatchResult]:
    """Detect orders in ledger with no settlement record yet (pending cash)."""
    results: List[MatchResult] = []
    settlement_order_ids = set()
    for stl in settlements:
        settlement_order_ids.update(stl.order_ids)

    for order in orders:
        if order.is_duplicate:
            continue
        if order.status == "disputed":
            continue
        if order.order_id not in settlement_order_ids:
            results.append(
                MatchResult(
                    entity_id=order.order_id,
                    entity_type="order",
                    tier="detector",
                    status="pending_settlement",
                    reasoning="Order exists in ledger but settlement has not landed yet - counts as 'pending' cash, not an unresolved exception.",
                    confidence=1.0,
                )
            )

    return results


def detect_disputed_chargebacks(orders: List[Order]) -> List[MatchResult]:
    """Detect disputed/chargeback orders that should stay in exception list."""
    results: List[MatchResult] = []
    for order in orders:
        if order.status == "disputed":
            results.append(
                MatchResult(
                    entity_id=order.order_id,
                    entity_type="order",
                    tier="detector",
                    status="exception_disputed_chargeback",
                    reasoning="Order disputed/charged back - correctly has NO settlement or bank counterpart. Should stay in exception list, not be force-matched.",
                    confidence=1.0,
                )
            )
    return results


def detect_partial_refunds(
    orders: List[Order],
    bank_txns: List[BankTxn],
) -> List[Tuple[Order, BankTxn]]:
    """Find order partial refund debit transactions in bank statement."""
    refund_pairs: List[Tuple[Order, BankTxn]] = []
    order_dict = {o.order_id: o for o in orders}

    for btx in bank_txns:
        if btx.txn_type == "debit" and "REFUND-ORD-" in btx.narration:
            parts = btx.narration.split("-")
            if len(parts) >= 3:
                oid = f"{parts[1]}-{parts[2]}"
                if oid in order_dict:
                    refund_pairs.append((order_dict[oid], btx))

    return refund_pairs


def detect_unrelated_bank_noise(
    settlements: List[Settlement],
    bank_txns: List[BankTxn],
) -> List[MatchResult]:
    """Identify unrelated bank activity (interest credit, AMB charges) with no order behind them."""
    results: List[MatchResult] = []
    settlement_utrs = {stl.utr for stl in settlements}

    for btx in bank_txns:
        if any(utr in btx.narration for utr in settlement_utrs):
            continue
        if "REFUND-ORD-" in btx.narration:
            continue

        results.append(
            MatchResult(
                entity_id=btx.bank_txn_id,
                entity_type="bank_txn",
                tier="detector",
                matched_bank_txn_id=btx.bank_txn_id,
                status="unrelated_bank_noise",
                reasoning=f"'{btx.narration}' is unrelated bank activity - correct system should leave this unmatched, not force it onto an order.",
                confidence=1.0,
            )
        )

    return results
