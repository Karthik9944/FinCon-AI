"""
Data models for the AI Finance Controller reconciliation engine.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Order:
    order_id: str
    order_date: str
    customer_name: str
    product: str
    amount_inr: float
    payment_method: str
    status: str  # 'created', 'partial_refund', 'disputed'
    is_duplicate: bool = False


@dataclass
class Settlement:
    settlement_id: str
    utr: str
    settlement_date: str
    order_ids: List[str]
    gross_amount: float
    razorpay_fee: float
    gst_on_fee: float
    tds: float
    net_amount: float


@dataclass
class BankTxn:
    bank_txn_id: str
    value_date: str
    amount: float
    txn_type: str  # 'credit' or 'debit'
    narration: str
    is_duplicate: bool = False


@dataclass
class MatchResult:
    entity_id: str
    entity_type: str  # 'order', 'settlement', 'bank_txn'
    tier: str  # 'tier1_exact_single', 'tier2_tolerance', 'tier3_many_to_one_batch', 'tier4_llm_agent', or edge bucket
    matched_settlement_id: Optional[str] = None
    matched_bank_txn_id: Optional[str] = None
    status: str = "unmatched"
    reasoning: str = ""
    confidence: float = 1.0


@dataclass
class AuditLogEntry:
    timestamp: str
    entity_id: str
    resolution_tier: str
    status: str
    reasoning: str
    confidence: float = 1.0


@dataclass
class CashRollup:
    total_ledger_gross: float = 0.0
    confirmed_settled_net: float = 0.0
    pending_settlement_net: float = 0.0
    bank_lag_settled_net: float = 0.0
    partial_refund_debits: float = 0.0
    disputed_exception_net: float = 0.0
    unrelated_bank_noise_net: float = 0.0
