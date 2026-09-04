"""
Tier 2 — Tolerance Matcher.
Handles paise rounding drift (e.g. 0.01 INR difference) and value date settlement lag.
"""

from typing import List, Set, Optional, Tuple
from datetime import datetime
from reconcile.models import Settlement, BankTxn, MatchResult


def check_date_lag_days(settlement_date_str: str, bank_date_str: str) -> int:
    """Calculate date difference in days (bank_date - settlement_date)."""
    d1 = datetime.strptime(settlement_date_str, "%Y-%m-%d")
    d2 = datetime.strptime(bank_date_str, "%Y-%m-%d")
    return (d2 - d1).days


def match_settlement_to_bank_with_tolerance(
    settlement: Settlement,
    bank_txns: List[BankTxn],
    matched_bank_txn_ids: Set[str],
    amount_tolerance: float = 0.05,
    max_lag_days: int = 5,
) -> Optional[Tuple[BankTxn, float, bool]]:
    """
    Find matching bank transaction credit for a settlement considering amount tolerance and date lag.
    Returns (matched_bank_txn, amount_diff, is_tolerance_applied).
    """
    for btx in bank_txns:
        if btx.bank_txn_id in matched_bank_txn_ids or btx.txn_type != "credit":
            continue

        if settlement.utr in btx.narration:
            amount_diff = abs(btx.amount - settlement.net_amount)
            if amount_diff <= amount_tolerance:
                lag = check_date_lag_days(settlement.settlement_date, btx.value_date)
                if 0 <= lag <= max_lag_days:
                    is_tolerance = (amount_diff > 0.001)
                    return btx, amount_diff, is_tolerance

    return None
