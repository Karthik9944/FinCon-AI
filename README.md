# AI Finance Controller — Razorpay Buildathon (Track 04)

> **Run the books and the cash position.**  
> An automated, multi-tier financial reconciliation controller that ingests internal order ledgers, Razorpay settlement reports, and bank statements, matches records deterministically, handles complex edge cases, computes real cash position rollups, and scores 100% accuracy against ground truth benchmarks.

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.9+

### 2. Run Reconciliation Engine & Audit Log
```bash
python reconcile.py
```
*Outputs structured audit trail to `audit_trail.json`.*

### 3. Run Ground Truth Verification & Scorecard
```bash
python score.py
```
*Evaluates the engine against `data/ground_truth.csv` and prints match rate & bucket accuracy.*

### 4. Launch Financial Controller Dashboard
```bash
streamlit run app.py
```
*Opens the dark-mode glassmorphic dashboard at `http://localhost:8501`.*

### 5. Run Unit Test Suite
```bash
python -m unittest discover tests
```

---

## 📊 Performance & Match Rate Results

Running `python score.py` yields the following verified benchmark results:

| Metric | Score | Status |
| :--- | :--- | :--- |
| **Ground Truth Bucket Accuracy** | **73 / 73 (100.00%)** | ✅ PERFECT MATCH |
| **Ledger Orders Reconciled** | **49 / 57 (85.96%)** | ✅ VERIFIED |
| **Pending & Lag State Categorization** | **11 / 11 (100.00%)** | ✅ VERIFIED |
| **Exception & Noise Classification** | **5 / 5 (100.00%)** | ✅ HONEST EXCEPTION LIST |

---

## 🏗️ Core Architecture & Tier Breakdown

The system follows a strict **deterministic-first** pipeline:

1. **Tier 1 — Exact Match**: Link single-order settlements directly to bank credits via UTR reference and exact net payout amount.
2. **Tier 2 — Tolerance Match**: Handle paise rounding drift ($\le 0.05$ INR) and value date settlement lag (0–5 days).
3. **Tier 3 — Aggregation Match**: Aggregate multi-order settlement batches (sum of $N$ orders $\approx$ settlement gross amount), validate fee/GST/TDS breakdown formulas, and link to bank payouts.
4. **Edge Case Detectors**: Pure rule-based classifiers for duplicate ledger rows, bank-side duplicate credits, settled-but-bank-lag timing states, pending settlements, partial refund debits, disputed chargebacks, and unrelated bank noise.
5. **Tier 4 — Isolated LLM Residual Agent & Guardrail**: Evaluates free-text bank narrations (e.g., `REFUND-ORD-1013-PARTIAL`). Requires confidence $\ge 0.85$ and structural order validation to accept a match.

---

## 🧮 Fee/GST/TDS Formula Assumptions

For Razorpay settlement batches:

$$\text{Razorpay Fee} = 2.0\% \times \text{Gross Amount}$$
$$\text{GST on Fee} = 18.0\% \times \text{Razorpay Fee}$$
$$\text{TDS} = 1.0\% \times \text{Gross Amount}$$
$$\text{Net Payout} = \text{Gross} - \text{Fee} - \text{GST} - \text{TDS}$$

The engine enforces $|\text{Calculated Net} - \text{Reported Net}| \le 0.05 \text{ INR}$ across all settlement batches.

---

## 📁 Repository Structure

```
.
├── reconcile.py               # Main CLI runner
├── score.py                   # Verification harness against ground_truth.csv
├── app.py                     # High-aesthetic Streamlit Financial Controller Dashboard
├── architecture.md            # Pipeline design & guardrails documentation
├── FAILURE_LOG.md             # Evidence of caught LLM failure & guardrail recovery
├── README.md                  # Setup & usage guide
├── data/                      # Input CSV source files
├── reconcile/                 # Core Python package
│   ├── loader.py              # Ingestion & schema normalizer
│   ├── models.py              # Data structures (Order, Settlement, BankTxn, Result)
│   ├── engine.py              # Tiered reconciliation pipeline orchestrator
│   ├── detectors.py           # Edge case detectors (duplicates, lag, refunds, noise)
│   ├── audit.py               # Audit logger
│   ├── cash_position.py       # Cash rollup calculator
│   └── tiers/                 # Matching tier algorithms (Tiers 1, 2, 3, 4)
└── tests/                     # Unit test suite (13 unit tests)
```
