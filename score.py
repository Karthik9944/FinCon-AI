#!/usr/bin/env python3
"""
Verification & Scoring Harness for AI Finance Controller.
Compares reconciliation engine output against data/ground_truth.csv.
"""

import os
import sys
from typing import Dict, List
from reconcile.loader import load_ground_truth, load_orders
from reconcile.engine import ReconciliationEngine


def score():
    data_dir = os.path.abspath("data")
    engine = ReconciliationEngine(data_dir=data_dir)
    entity_primary_results, entity_buckets = engine.run()
    gt = load_ground_truth(data_dir)

    total_gt = len(gt)
    matched_gt_count = 0
    mismatches: List[Dict] = []
    bucket_counts: Dict[str, int] = {}
    tier_counts: Dict[str, int] = {}

    for row in gt:
        oid = row["order_id"]
        expected_bucket = row["expected_bucket"]
        bucket_counts[expected_bucket] = bucket_counts.get(expected_bucket, 0) + 1

        actual_buckets = entity_buckets.get(oid, set())
        primary_res = entity_primary_results.get(oid)

        if expected_bucket in actual_buckets:
            matched_gt_count += 1
            tier = primary_res.tier if primary_res else expected_bucket
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        else:
            mismatches.append({
                "id": oid,
                "expected": expected_bucket,
                "actual_buckets": list(actual_buckets),
                "notes": row["notes"],
                "reasoning": primary_res.reasoning if primary_res else "No result",
            })

    gt_accuracy_pct = (matched_gt_count / total_gt) * 100.0 if total_gt > 0 else 0.0

    # Calculate Order Settlement Match Rate
    orders = load_orders(data_dir)
    total_ledger_orders = len([o for o in orders if not o.is_duplicate])
    matched_settled_orders = len([
        r for r in entity_primary_results.values()
        if r.status in ("tier1_exact_single", "tier3_many_to_one_batch", "partial_refund") and r.entity_type == "order"
    ])
    order_match_rate_pct = (matched_settled_orders / total_ledger_orders) * 100.0 if total_ledger_orders > 0 else 0.0

    print("================================================================================")
    print("           AI FINANCE CONTROLLER -- GROUND TRUTH RECONCILIATION SCORECARD        ")
    print("================================================================================\n")
    print(f"Total Ground Truth Evaluated Items: {total_gt}")
    print(f"Ground Truth Bucket Accuracy Score: {matched_gt_count} / {total_gt} ({gt_accuracy_pct:.2f}%)\n")
    print(f"Ledger Orders Reconciled:           {matched_settled_orders} / {total_ledger_orders} ({order_match_rate_pct:.2f}%)\n")

    print("--------------------------------------------------------------------------------")
    print("                        BREAKDOWN BY RESOLUTION TIER                           ")
    print("--------------------------------------------------------------------------------")
    for tier_name, count in sorted(tier_counts.items()):
        print(f"  * {tier_name:<30}: {count:>3} records")
    print()

    print("--------------------------------------------------------------------------------")
    print("                     CATEGORIZED GROUND TRUTH BUCKET STATS                     ")
    print("--------------------------------------------------------------------------------")
    for b_name, count in sorted(bucket_counts.items()):
        print(f"  * {b_name:<30}: {count:>3} records")
    print()

    if mismatches:
        print("--------------------------------------------------------------------------------")
        print("                            MISMATCHED RECORDS DETECTED                          ")
        print("--------------------------------------------------------------------------------")
        for m in mismatches:
            print(f" [!] ID: {m['id']}")
            print(f"     Expected: {m['expected']}")
            print(f"     Actual:   {m['actual_buckets']}")
            print(f"     Notes:    {m['notes']}")
            print(f"     Engine:   {m['reasoning']}\n")
    else:
        print("================================================================================")
        print("   [SUCCESS] PERFECT 100% GROUND TRUTH ALIGNMENT -- ALL BUCKETS VERIFIED!       ")
        print("================================================================================\n")

    return mismatches


if __name__ == "__main__":
    mismatches = score()
    if mismatches:
        sys.exit(1)
    else:
        sys.exit(0)
