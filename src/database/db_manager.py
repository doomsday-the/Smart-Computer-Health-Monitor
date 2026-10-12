"""
SQLite Database Manager.
Provides thread-safe connections, migrations, parameterized queries, and persistence methods.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.database.schema import CREATE_TABLES_SQL, SCHEMA_VERSION

logger = logging.getLogger("HealthMonitor.Database")


class DatabaseManager:
    """Manages SQLite database connections, schema setup, and queries."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initialize the database schema if not already created."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.executescript(CREATE_TABLES_SQL)
                    cur = conn.cursor()
                    cur.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1;")
                    row = cur.fetchone()
                    if not row:
                        cur.execute("INSERT INTO schema_info (version) VALUES (?);", (SCHEMA_VERSION,))
                    conn.commit()
                logger.info(f"Database initialized successfully at {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}", exc_info=True)
                raise

    # ------------------ System Metrics ------------------

    def insert_system_metric(self, metric: Dict[str, Any]) -> int:
        """Insert a system metric reading. Returns the row ID."""
        sql = """
        INSERT INTO system_metrics (
            timestamp, cpu_percent, cpu_frequency, ram_percent,
            ram_used_bytes, ram_available_bytes, ram_total_bytes,
            disk_used_bytes, disk_free_bytes, disk_total_bytes, disk_percent,
            disk_read_bytes, disk_write_bytes, battery_percent, battery_plugged,
            health_score
        ) VALUES (
            :timestamp, :cpu_percent, :cpu_frequency, :ram_percent,
            :ram_used_bytes, :ram_available_bytes, :ram_total_bytes,
            :disk_used_bytes, :disk_free_bytes, :disk_total_bytes, :disk_percent,
            :disk_read_bytes, :disk_write_bytes, :battery_percent, :battery_plugged,
            :health_score
        )
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, metric)
                conn.commit()
                return cur.lastrowid

    def get_recent_metrics(self, limit: int = 60) -> List[Dict[str, Any]]:
        """Fetch the most recent N metric records in chronological order."""
        sql = """
        SELECT * FROM (
            SELECT * FROM system_metrics ORDER BY id DESC LIMIT ?
        ) ORDER BY id ASC;
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (limit,))
                return [dict(row) for row in cur.fetchall()]

    def get_metrics_in_range(self, start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
        """Fetch metric records within an ISO timestamp range."""
        sql = """
        SELECT * FROM system_metrics
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC;
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (start_iso, end_iso))
                return [dict(row) for row in cur.fetchall()]

    def get_metrics_time_window(self, minutes: int) -> List[Dict[str, Any]]:
        """Fetch metrics for the past N minutes."""
        since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        sql = """
        SELECT * FROM system_metrics
        WHERE timestamp >= ?
        ORDER BY timestamp ASC;
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (since,))
                return [dict(row) for row in cur.fetchall()]

    # ------------------ Process Snapshots ------------------

    def insert_process_snapshots(self, timestamp: str, processes: List[Dict[str, Any]]) -> None:
        """Bulk insert process snapshots for a specific timestamp."""
        sql = """
        INSERT INTO process_snapshots (
            timestamp, pid, process_name, cpu_percent, memory_percent,
            memory_used_bytes, process_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        records = [
            (
                timestamp,
                p.get("pid", 0),
                p.get("name", "unknown"),
                p.get("cpu_percent", 0.0),
                p.get("memory_percent", 0.0),
                p.get("memory_used_bytes", 0),
                p.get("status", "running")
            )
            for p in processes
        ]
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.executemany(sql, records)
                conn.commit()

    def get_recent_process_snapshots(self, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the latest process snapshots."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if not timestamp:
                    cur.execute("SELECT timestamp FROM process_snapshots ORDER BY id DESC LIMIT 1;")
                    row = cur.fetchone()
                    if not row:
                        return []
                    timestamp = row["timestamp"]
                cur.execute(
                    "SELECT * FROM process_snapshots WHERE timestamp = ? ORDER BY cpu_percent DESC;",
                    (timestamp,)
                )
                return [dict(r) for r in cur.fetchall()]

    # ------------------ Insights ------------------

    def upsert_insight(self, insight: Dict[str, Any]) -> None:
        """Insert or update an insight."""
        sql = """
        INSERT INTO insights (
            id, created_at, updated_at, resource, severity, title,
            observed_value, rule_triggered, explanation, evidence_json,
            possible_cause, confidence_label, recommendation, status, resolved_at
        ) VALUES (
            :id, :created_at, :updated_at, :resource, :severity, :title,
            :observed_value, :rule_triggered, :explanation, :evidence_json,
            :possible_cause, :confidence_label, :recommendation, :status, :resolved_at
        )
        ON CONFLICT(id) DO UPDATE SET
            updated_at = excluded.updated_at,
            severity = excluded.severity,
            observed_value = excluded.observed_value,
            explanation = excluded.explanation,
            evidence_json = excluded.evidence_json,
            possible_cause = excluded.possible_cause,
            recommendation = excluded.recommendation,
            status = excluded.status,
            resolved_at = excluded.resolved_at;
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, insight)
                conn.commit()

    def get_active_insights(self) -> List[Dict[str, Any]]:
        """Return all ongoing or new insights."""
        sql = """
        SELECT * FROM insights
        WHERE status IN ('new', 'ongoing')
        ORDER BY 
            CASE severity
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                ELSE 3
            END,
            updated_at DESC;
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchall()
                result = []
                for r in rows:
                    item = dict(r)
                    if item.get("evidence_json"):
                        try:
                            item["evidence"] = json.loads(item["evidence_json"])
                        except Exception:
                            item["evidence"] = {}
                    result.append(item)
                return result

    def get_all_insights(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return insights history."""
        sql = "SELECT * FROM insights ORDER BY updated_at DESC LIMIT ?;"
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (limit,))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    item = dict(r)
                    if item.get("evidence_json"):
                        try:
                            item["evidence"] = json.loads(item["evidence_json"])
                        except Exception:
                            item["evidence"] = {}
                    result.append(item)
                return result

    # ------------------ Alerts ------------------

    def insert_alert(self, alert: Dict[str, Any]) -> int:
        """Insert an alert record."""
        sql = """
        INSERT INTO alerts (insight_id, timestamp, severity, resource, message, acknowledged, resolved)
        VALUES (:insight_id, :timestamp, :severity, :resource, :message, :acknowledged, :resolved);
        """
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, alert)
                conn.commit()
                return cur.lastrowid

    def get_alerts(self, only_active: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch alerts with optional filtering."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if only_active:
                    cur.execute(
                        "SELECT * FROM alerts WHERE resolved = 0 ORDER BY id DESC LIMIT ?;",
                        (limit,)
                    )
                else:
                    cur.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?;", (limit,))
                return [dict(r) for r in cur.fetchall()]

    def acknowledge_alert(self, alert_id: int) -> bool:
        """Mark an alert as acknowledged."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?;", (alert_id,))
                conn.commit()
                return cur.rowcount > 0

    def resolve_alert(self, alert_id: int) -> bool:
        """Mark an alert as resolved."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE alerts SET resolved = 1 WHERE id = ?;", (alert_id,))
                conn.commit()
                return cur.rowcount > 0

    def resolve_alerts_for_insight(self, insight_id: str) -> int:
        """Mark all alerts for a given insight as resolved."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE alerts SET resolved = 1 WHERE insight_id = ?;", (insight_id,))
                conn.commit()
                return cur.rowcount

    # ------------------ Settings ------------------

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a setting value by key."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM settings WHERE key = ?;", (key,))
                row = cur.fetchone()
                return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Save a setting value."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
                    (key, value)
                )
                conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        """Retrieve all stored settings."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT key, value FROM settings;")
                return {row["key"]: row["value"] for row in cur.fetchall()}

    # ------------------ Maintenance ------------------

    def purge_old_data(self, retention_days: int) -> Dict[str, int]:
        """Delete metrics and process snapshots older than retention days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM system_metrics WHERE timestamp < ?;", (cutoff,))
                metrics_deleted = cur.rowcount
                cur.execute("DELETE FROM process_snapshots WHERE timestamp < ?;", (cutoff,))
                procs_deleted = cur.rowcount
                conn.commit()
                return {"metrics_deleted": metrics_deleted, "procs_deleted": procs_deleted}

    def clear_all_history(self) -> None:
        """Clear all historical metric and alert tables."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM alerts;")
                cur.execute("DELETE FROM insights;")
                cur.execute("DELETE FROM process_snapshots;")
                cur.execute("DELETE FROM system_metrics;")
                conn.commit()
                logger.info("Cleared all historical monitoring data.")
