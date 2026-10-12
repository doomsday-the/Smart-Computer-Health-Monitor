"""
Tests for AlertManager.
Validates duplicate alert suppression, cooldown mechanics, severity escalation,
and lifecycle resolution tracking.
"""

import time
import pytest
from pathlib import Path
from src.config import MonitorSettings
from src.database.db_manager import DatabaseManager
from src.analysis.interpretation_engine import Insight
from src.alerts.alert_manager import AlertManager


def create_test_insight(ins_id="cpu_issue", severity="warning", status="new"):
    return Insight(
        id=ins_id,
        resource="CPU",
        severity=severity,
        title="Elevated CPU Load",
        observed_value="78%",
        rule_triggered="Exceeds 70%",
        explanation="Testing explanation",
        evidence={},
        possible_cause="Test cause",
        confidence_label="High",
        recommendation="Inspect processes",
        status=status,
        created_at="2026-10-10T12:00:00Z",
        updated_at="2026-10-10T12:00:00Z"
    )


def test_alert_suppression_and_escalation(tmp_path: Path):
    db_file = tmp_path / "test_alerts.db"
    db = DatabaseManager(db_file)
    settings = MonitorSettings(alert_cooldown_sec=10.0)
    manager = AlertManager(db, settings)

    # 1. First trigger: should emit an alert
    ins = create_test_insight(severity="warning", status="new")
    alerts1 = manager.process_insights([ins])
    assert len(alerts1) == 1
    assert alerts1[0].severity == "warning"

    # 2. Immediate second cycle (ongoing warning, within cooldown): MUST be suppressed!
    ins.status = "ongoing"
    alerts2 = manager.process_insights([ins])
    assert len(alerts2) == 0  # Deduplication suppressed duplicate

    # 3. Severity escalates to Critical: should emit escalation alert immediately
    ins.severity = "critical"
    alerts3 = manager.process_insights([ins])
    assert len(alerts3) == 1
    assert alerts3[0].severity == "critical"

    # 4. Condition resolves: should mark alert as resolved in DB
    ins.status = "resolved"
    manager.process_insights([ins])
    active = manager.get_active_alerts()
    assert len(active) == 0


def test_alert_acknowledgement_and_manual_resolve(tmp_path: Path):
    db_file = tmp_path / "test_alerts_ack.db"
    db = DatabaseManager(db_file)
    settings = MonitorSettings()
    manager = AlertManager(db, settings)

    ins = create_test_insight(severity="critical", status="new")
    alerts = manager.process_insights([ins])
    assert len(alerts) == 1
    alert_id = alerts[0].id

    # Acknowledge
    assert manager.acknowledge_alert(alert_id) is True
    # Resolve
    assert manager.resolve_alert(alert_id) is True

    # Active alerts should now be empty
    active = manager.get_active_alerts()
    assert len(active) == 0
