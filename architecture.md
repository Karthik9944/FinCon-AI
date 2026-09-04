# Pipeline Architecture — AI Finance Controller(FinCon AI)

## Philosophy: Deterministic-First, AI Only for Residuals

The core design principle of this financial reconciliation controller is **deterministic logic primacy**. In financial ops, auditing accuracy, speed, and reproducibility are non-negotiable. Passing every record through an LLM is slow, expensive, non-deterministic, and prone to silent hallucinations.

Our architecture enforces a strict pipeline:
1. **Tiers 1–3**: 100% deterministic Python rules that match structured references (UTR, Order IDs), enforce financial formulas ($Net = Gross - Fee - GST - TDS$), and handle amount/date tolerances.
2. **Edge Case Detectors**: Pure rule-based classifiers that identify duplicate ledger rows, duplicate bank credits, settled-but-bank-lag timing states, pending settlements, partial refunds, chargebacks, and bank noise.
3. **Tier 4 (LLM Agent)**: Reserved **exclusively** for residual items (e.g. unstructured, free-text bank narrations like `REFUND-ORD-1013-PARTIAL`).

```
+---------------------------------------------------------------------------------------------------+
|                                     CSV DATA INGESTION ENGINE                                     |
|                      [orders_ledger.csv] [settlement_report.csv] [bank_statement.csv]             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|  TIER 1: EXACT MATCHING                                                                           |
|  Matches single-order settlements directly linked to bank credits via UTR and exact net amount.  |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|  TIER 2 & 3: AGGREGATION & TOLERANCE MATCHING                                                     |
|  - Aggregates multi-order settlement batches (sum of order amounts ≈ gross amount).               |
|  - Verifies fee breakdown: Net = Gross - Fee - GST_on_fee - TDS                                   |
|  - Matches settlement net amount to bank credit row (allows ±0.05 INR rounding drift & 0-5d lag). |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|  EDGE CASE DETECTORS                                                                              |
|  - Duplicate Ledger Rows (e.g., ORD-1035-DUP)                                                     |
|  - Duplicate Bank Credits (e.g., SETL-2008 bank-side duplicate credits)                           |
|  - Settled-but-Bank-Lag (Razorpay settled, bank credit pending)                                   |
|  - Pending Settlement (Ledger order created, no settlement yet)                                   |
|  - Disputed / Chargeback Exceptions                                                               |
|  - Unrelated Bank Noise (Interest credit, maintenance charges)                                    |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|  TIER 4: ISOLATED LLM RESIDUAL AGENT & SAFETY GUARDRAIL                                           |
|  - Evaluates unstructured narrations (e.g., REFUND-ORD-1013-PARTIAL).                             |
|  - Assigns confidence score & stated reasoning.                                                   |
|  - GUARDRAIL: Requires confidence ≥ 0.85 & order ID existence check.                              |
|  - Low confidence / speculative proposals are REJECTED and kept in the exception list.            |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                 AUDIT LOG & CASH POSITION ROLLUP                                  |
|                 [audit_trail.json] [score.py (100% Match)] [app.py (Streamlit UI)]                |
+---------------------------------------------------------------------------------------------------+
```

---

## Razorpay Fee/GST/TDS Formula Assumptions

For Razorpay settlement batches, gross order amounts are reconciled against net bank payouts using the standard Indian payment gateway fee structure:

$$\text{Razorpay Fee} = 2.0\% \times \text{Gross Amount}$$
$$\text{GST on Fee} = 18.0\% \times \text{Razorpay Fee}$$
$$\text{TDS Deducted} = 1.0\% \times \text{Gross Amount}$$
$$\text{Calculated Net Payout} = \text{Gross Amount} - \text{Razorpay Fee} - \text{GST on Fee} - \text{TDS Deducted}$$

### Formula Validation Rule
In `reconcile/tiers/tier3_aggregation.py`, the calculated net payout is checked against the settlement report net amount:
$$|\text{Calculated Net} - \text{Settlement Net Amount}| \le 0.05 \text{ INR}$$

Any settlement batch violating this tolerance threshold is flagged for manual finance-ops audit.

---

## AI Agent Guardrails & Failure Recovery

The Tier 4 LLM agent handles free-text bank narrations. To protect against AI hallucinations:

1. **Isolation**: Tiers 1–3 contain zero LLM dependencies and run pure Python code.
2. **Confidence Threshold**: Set at **0.85**. Proposals with confidence below 0.85 are automatically rejected.
3. **Structural Verification**: Proposed order IDs are validated against the actual ledger.
4. **Offline Fallback**: When running without API keys or in offline test environments, a rule-based parser provides deterministic, reproducible behavior matching the exact confidence scoring rules.

See [FAILURE_LOG.md](file:///e:/AI%20Finance%20Controller/FAILURE_LOG.md) for concrete evidence of a caught and rejected low-confidence proposal.
