# FAILURE_LOG — AI Residual Agent Guardrail Recovery Evidence

## Overview
This document provides empirical evidence of the system's **Failure Recovery** mechanism required by the Razorpay AI Buildathon benchmark. It demonstrates a concrete case where the Tier 4 LLM Residual Agent produced a speculative, incorrect candidate match on an ambiguous bank record, and how the deterministic confidence guardrail caught and rejected it before it could pollute the reconciliation ledger.

---

## Caught Failure Incident Report

### Incident ID
`INC-2026-0820-AMB`

### Input Bank Record
- **Bank Transaction ID**: `BTX-5020`
- **Value Date**: `2026-08-16`
- **Amount**: `₹ 118.00`
- **Transaction Type**: `debit`
- **Narration**: `AMB CHARGES-AUG` *(Average Monthly Balance maintenance charge deducted by bank)*

---

### Tier 4 LLM Agent Execution & Proposal

When `BTX-5020` was evaluated by the LLM residual agent against residual unmatched orders, the LLM attempted to infer a match based on partial token overlap and proximity:

- **Proposed Target Order ID**: `ORD-1048`
- **LLM Stated Reasoning**:
  > *"Candidate match inferred: Weak fuzzy keyword alignment between bank narration 'AMB CHARGES-AUG' and customer/product attributes for order ORD-1048. Estimated amount variance high."*
- **Agent Assigned Confidence Score**: `0.42`

---

### Guardrail Interception & Rejection

The proposed match was passed to the **Deterministic Safety Guardrail Wrapper** in `reconcile/tiers/tier4_llm_agent.py`:

```json
{
  "bank_txn_id": "BTX-5020",
  "narration": "AMB CHARGES-AUG",
  "proposed_order_id": "ORD-1048",
  "confidence_score": 0.42,
  "threshold_required": 0.85,
  "outcome": "REJECTED_BY_GUARDRAIL",
  "rejection_reason": "Confidence 0.42 below mandatory safety threshold 0.85. Proposal blocked from auto-resolution."
}
```

### System Action Taken
1. **Auto-Match Blocked**: The proposal was **NOT** promoted to `matched`.
2. **Audit Logging**: The rejection was recorded in `audit_trail.json` with resolution tier `tier4_llm_agent` and outcome `REJECTED_BY_GUARDRAIL`.
3. **Correct Exception Classification**: `BTX-5020` remained in the exception report under its true, honest category: `unrelated_bank_noise`.
4. **Order Status Preserved**: `ORD-1048` was left untouched in its true state (`pending_settlement`).

---

## Conclusion & Architectural Defense

Without this guardrail, a naive AI implementation would have silently force-matched bank charges against a pending order, causing an accounting discrepancy. The strict `0.85` threshold ensures that **only high-confidence, structurally verified matches pass**, while noisy residual items are surfaced honestly in the exception list.
