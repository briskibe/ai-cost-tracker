"""SQLite storage backend for cost logs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .models import CostLog


class SQLiteStorage:
    """SQLite-backed storage for cost tracking events."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        db_parent = Path(db_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Create required schema and indexes if they do not exist."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cost_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    feature TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    org_id TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cost_logs_user_id ON cost_logs(user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cost_logs_feature ON cost_logs(feature)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cost_logs_timestamp ON cost_logs(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cost_logs_org_id ON cost_logs(org_id)"
            )
            self._conn.commit()

    def close(self) -> None:
        """Close the SQLite connection."""
        with self._lock:
            self._conn.close()

    def log(self, cost_log: CostLog) -> None:
        """Persist a cost log entry."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO cost_logs (
                    user_id, feature, model, tokens_in, tokens_out,
                    cost_usd, latency_ms, timestamp, org_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cost_log.user_id,
                    cost_log.feature,
                    cost_log.model,
                    cost_log.tokens_in,
                    cost_log.tokens_out,
                    cost_log.cost_usd,
                    cost_log.latency_ms,
                    cost_log.timestamp.isoformat(),
                    cost_log.org_id,
                    json.dumps(cost_log.metadata, ensure_ascii=True),
                ),
            )
            self._conn.commit()

    def get_total_cost(self, filters: Optional[Dict[str, Any]] = None) -> float:
        """Return total cost in USD for optional filters."""
        where_sql, params = self._build_where_clause(filters)
        query = f"SELECT COALESCE(SUM(cost_usd), 0.0) AS total FROM cost_logs {where_sql}"

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return float(row["total"] if row is not None else 0.0)

    def get_top_users(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, int]]:
        """Return top users as `(user_id, total_cost, call_count)` tuples."""
        where_sql, params = self._build_where_clause(filters)
        query = (
            "SELECT user_id, SUM(cost_usd) AS total, COUNT(*) AS call_count "
            f"FROM cost_logs {where_sql} "
            "GROUP BY user_id ORDER BY total DESC LIMIT ?"
        )

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, (*params, limit))
            rows = cursor.fetchall()
            return [(row["user_id"], float(row["total"]), int(row["call_count"])) for row in rows]

    def get_top_features(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, int]]:
        """Return top features as `(feature, total_cost, call_count)` tuples."""
        where_sql, params = self._build_where_clause(filters)
        query = (
            "SELECT feature, SUM(cost_usd) AS total, COUNT(*) AS call_count "
            f"FROM cost_logs {where_sql} "
            "GROUP BY feature ORDER BY total DESC LIMIT ?"
        )

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, (*params, limit))
            rows = cursor.fetchall()
            return [(row["feature"], float(row["total"]), int(row["call_count"])) for row in rows]

    def _build_where_clause(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Sequence[Any]]:
        if not filters:
            return "", ()

        clauses: List[str] = []
        params: List[Any] = []

        simple_fields = ("user_id", "feature", "org_id", "model")
        for field in simple_fields:
            value = filters.get(field)
            if value is not None:
                clauses.append(f"{field} = ?")
                params.append(value)

        if filters.get("start_time") is not None:
            clauses.append("timestamp >= ?")
            params.append(filters["start_time"])

        if filters.get("end_time") is not None:
            clauses.append("timestamp <= ?")
            params.append(filters["end_time"])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, tuple(params)
