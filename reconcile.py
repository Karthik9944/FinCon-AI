#!/usr/bin/env python3
"""
CLI entrypoint for running the AI Finance Controller Reconciliation Engine.
"""

import sys
import os
import argparse
from reconcile.engine import ReconciliationEngine


def main():
    parser = argparse.ArgumentParser(description="AI Finance Controller — Tiered Financial Reconciliation Pipeline")
    parser.add_argument("--data-dir", default="data", help="Directory containing source CSV files (default: data)")
    parser.add_argument("--audit-out", default="audit_trail.json", help="Path for exporting structured audit log")
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    print(f"=== AI Finance Controller — Starting Reconciliation Pipeline ===")
    print(f"Ingesting CSV data from: {data_dir}\n")

    engine = ReconciliationEngine(data_dir=data_dir)
    entity_results, all_results = engine.run()

    print(f"Pipeline Execution Complete.")
    print(f"Total Resolution Records Processed: {len(entity_results)}")
    
    # Export audit trail
    engine.audit_logger.export_json(args.audit_out)
    print(f"Audit log exported to: {args.audit_out}\n")


if __name__ == "__main__":
    main()
