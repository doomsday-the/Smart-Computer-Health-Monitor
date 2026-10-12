"""
Alert Manager module.
Handles alert generation, state transitions, deduplication suppression,
cooldown timers, acknowledgement, and resolution tracking in the database.
"""

import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from src.config import MonitorSettings
from src.analysis.interpretation_engine import Insight
from src.database.db_manager import DatabaseManager

logger = logging.getLogger("HealthMonitor.AlertManager")


@dataclass
class AlertItem:
    id: Optional[int]
    insight_id: str
    timestamp: str
    severity: str  # info, warning, critical
    resource: str
    message: str
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlertManager:
    """Coordinates alert lifecycle, database persistence, and duplicate suppression."""

    def __init__(self, db_manager: DatabaseManager, settings: MonitorSettings):
        self.db = db_manager
        self.settings = settings
        
        # In-memory deduplication tracking:
        # Key: insight_id -> {"last_emitted_time": float, "last_severity": str, "alert_id": int}
        self._last_alert_state: Dict[str, Dict[str, Any]] = {}

    def update_settings(self, settings: MonitorSettings) -> None:
        self.settings = settings

    def process_insights(self, insights: List[Insight]) -> List[AlertItem]:
        """
        Evaluate insights and generate new alerts only when appropriate
        (suppressing duplicate notifications for existing ongoing conditions).
        """
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        new_alerts: List[AlertItem] = []

        for ins in insights:
            if ins.status in ("new", "ongoing"):
                state = self._last_alert_state.get(ins.id)
                should_emit = False

                if state is None:
                    # New condition: emit immediately
                    should_emit = True
                elif state["last_severity"] != ins.severity:
                    # Severity escalated or changed: emit update
                    should_emit = True
                elif (now_ts - state["last_emitted_time"]) >= self.settings.alert_cooldown_sec:
                    # Cooldown has expired on continuing condition
                    should_emit = True

                if should_emit:
                    message = f"{ins.title}: {ins.observed_value}. {ins.recommendation}"
                    alert_record = {
                        "insight_id": ins.id,
                        "timestamp": now_iso,
                        "severity": ins.severity,
                        "resource": ins.resource,
                        "message": message,
                        "acknowledged": 0,
                        "resolved": 0
                    }
                    try:
                        self.db.upsert_insight(ins.to_dict())
                        row_id = self.db.insert_alert(alert_record)
                        self._last_alert_state[ins.id] = {
                            "last_emitted_time": now_ts,
                            "last_severity": ins.severity,
                            "alert_id": row_id
                        }
                        item = AlertItem(
                            id=row_id,
                            insight_id=ins.id,
                            timestamp=now_iso,
                            severity=ins.severity,
                            resource=ins.resource,
                            message=message,
                            acknowledged=False,
                            resolved=False
                        )
                        new_alerts.append(item)
                    except Exception as e:
                        logger.error(f"Failed to persist alert: {e}")

            elif ins.status == "resolved":
                # Condition recovered: resolve any active alerts for this insight
                if ins.id in self._last_alert_state:
                    try:
                        self.db.resolve_alerts_for_insight(ins.id)
                    except Exception as e:
                        logger.error(f"Error resolving alerts for insight {ins.id}: {e}")
                    del self._last_alert_state[ins.id]

        return new_alerts

    def acknowledge_alert(self, alert_id: int) -> bool:
        """User marks an alert as acknowledged."""
        return self.db.acknowledge_alert(alert_id)

    def resolve_alert(self, alert_id: int) -> bool:
        """User marks an alert as manually resolved."""
        return self.db.resolve_alert(alert_id)

    def get_active_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch unresolved alerts from the database."""
        return self.db.get_alerts(only_active=True, limit=limit)

    def get_all_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all historical alerts."""
        return self.db.get_alerts(only_active=False, limit=limit)
