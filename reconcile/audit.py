"""
Audit logger for logging reconciliation steps with resolution tier, reasoning, and timestamp.
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any
from reconcile.models import AuditLogEntry, MatchResult


class AuditLogger:
    def __init__(self):
        self.entries: List[AuditLogEntry] = []

    def log(self, entity_id: str, resolution_tier: str, status: str, reasoning: str, confidence: float = 1.0) -> AuditLogEntry:
        timestamp = datetime.now().isoformat()
        entry = AuditLogEntry(
            timestamp=timestamp,
            entity_id=entity_id,
            resolution_tier=resolution_tier,
            status=status,
            reasoning=reasoning,
            confidence=confidence,
        )
        self.entries.append(entry)
        return entry

    def log_result(self, result: MatchResult) -> AuditLogEntry:
        return self.log(
            entity_id=result.entity_id,
            resolution_tier=result.tier,
            status=result.status,
            reasoning=result.reasoning,
            confidence=result.confidence,
        )

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": e.timestamp,
                "entity_id": e.entity_id,
                "resolution_tier": e.resolution_tier,
                "status": e.status,
                "reasoning": e.reasoning,
                "confidence": e.confidence,
            }
            for e in self.entries
        ]

    def export_json(self, file_path: str):
        with open(file_path, mode="w", encoding="utf-8") as f:
            json.dump(self.to_dict_list(), f, indent=2)

    def export_csv(self, file_path: str):
        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "entity_id", "resolution_tier", "status", "reasoning", "confidence"])
            for e in self.entries:
                writer.writerow([e.timestamp, e.entity_id, e.resolution_tier, e.status, e.reasoning, e.confidence])
