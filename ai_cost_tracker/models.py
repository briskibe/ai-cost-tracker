"""Data models for cost tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class CostLog:
    """Single record of LLM usage cost."""

    user_id: str
    feature: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    org_id: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this log entry as a JSON-friendly dictionary."""
        return {
            "user_id": self.user_id,
            "feature": self.feature,
            "model": self.model,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "org_id": self.org_id,
            "metadata": self.metadata,
        }
