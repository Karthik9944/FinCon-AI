"""
Data loader module for ingesting CSV sources with schema normalization.
"""

import csv
import os
from typing import List, Tuple, Dict, Any
from reconcile.models import Order, Settlement, BankTxn


def find_file(directory: str, primary_name: str, fallback_names: List[str]) -> str:
    """Find file in directory using primary name or fallback alternatives."""
    path = os.path.join(directory, primary_name)
    if os.path.exists(path):
        return path
    for fb in fallback_names:
        path = os.path.join(directory, fb)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not find {primary_name} or fallbacks {fallback_names} in {directory}")


def load_orders(data_dir: str) -> List[Order]:
    """Load order ledger records from CSV."""
    file_path = find_file(data_dir, "orders_ledger.csv", ["orders_ledger (1).csv", "orders_ledger.CSV"])
    orders: List[Order] = []
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orders.append(
                Order(
                    order_id=row["order_id"].strip(),
                    order_date=row["order_date"].strip(),
                    customer_name=row["customer_name"].strip(),
                    product=row["product"].strip(),
                    amount_inr=float(row["amount_inr"]),
                    payment_method=row["payment_method"].strip(),
                    status=row["status"].strip(),
                )
            )
    return orders


def load_settlements(data_dir: str) -> List[Settlement]:
    """Load Razorpay settlement report records from CSV."""
    file_path = find_file(data_dir, "settlement_report.csv", ["settlement_report.CSV"])
    settlements: List[Settlement] = []
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_order_ids = row["order_ids"].strip()
            order_ids = [oid.strip() for oid in raw_order_ids.split(";") if oid.strip()]
            settlements.append(
                Settlement(
                    settlement_id=row["settlement_id"].strip(),
                    utr=row["utr"].strip(),
                    settlement_date=row["settlement_date"].strip(),
                    order_ids=order_ids,
                    gross_amount=float(row["gross_amount"]),
                    razorpay_fee=float(row["razorpay_fee"]),
                    gst_on_fee=float(row["gst_on_fee"]),
                    tds=float(row["tds"]),
                    net_amount=float(row["net_amount"]),
                )
            )
    return settlements


def load_bank_transactions(data_dir: str) -> List[BankTxn]:
    """Load bank statement records from CSV."""
    file_path = find_file(data_dir, "bank_statement.csv", ["bank_statement.CSV"])
    txns: List[BankTxn] = []
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            txns.append(
                BankTxn(
                    bank_txn_id=row["bank_txn_id"].strip(),
                    value_date=row["value_date"].strip(),
                    amount=float(row["amount"]),
                    txn_type=row["type"].strip().lower(),
                    narration=row["narration"].strip(),
                )
            )
    return txns


def load_ground_truth(data_dir: str) -> List[Dict[str, str]]:
    """Load ground truth answer key for verification."""
    file_path = find_file(data_dir, "ground_truth.csv", ["ground_truth.CSV"])
    rows: List[Dict[str, str]] = []
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "order_id": row["order_id"].strip(),
                "expected_bucket": row["expected_bucket"].strip(),
                "notes": row["notes"].strip(),
            })
    return rows
