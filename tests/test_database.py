"""
Tests for DatabaseManager and SQLite schema.
Validates table creation, parameterized inserts, queries, migrations,
settings persistence, and safe history purge.
"""

from pathlib import Path
from src.database.db_manager import DatabaseManager


def test_db_init_and_metrics_crud(tmp_path: Path):
    db_file = tmp_path / "test_health.db"
    db = DatabaseManager(db_file)

    # Insert Metric
    metric = {
        "timestamp": "2026-10-10T12:00:00Z",
        "cpu_percent": 42.5,
        "cpu_frequency": 3400.0,
        "ram_percent": 60.0,
        "ram_used_bytes": 8 * 1024**3,
        "ram_available_bytes": 8 * 1024**3,
        "ram_total_bytes": 16 * 1024**3,
        "disk_used_bytes": 200 * 1024**3,
        "disk_free_bytes": 300 * 1024**3,
        "disk_total_bytes": 500 * 1024**3,
        "disk_percent": 40.0,
        "disk_read_bytes": 50000,
        "disk_write_bytes": 80000,
        "battery_percent": 85.0,
        "battery_plugged": 1,
        "health_score": 92.0
    }
    row_id = db.insert_system_metric(metric)
    assert row_id > 0

    recent = db.get_recent_metrics(limit=10)
    assert len(recent) == 1
    assert recent[0]["cpu_percent"] == 42.5
    assert recent[0]["health_score"] == 92.0


def test_process_snapshots_and_insights(tmp_path: Path):
    db_file = tmp_path / "test_procs.db"
    db = DatabaseManager(db_file)

    ts = "2026-10-10T12:05:00Z"
    procs = [
        {"pid": 101, "name": "editor.exe", "cpu_percent": 5.0, "memory_percent": 10.0, "memory_used_bytes": 50000000, "status": "running"},
        {"pid": 102, "name": "rustc.exe", "cpu_percent": 80.0, "memory_percent": 25.0, "memory_used_bytes": 200000000, "status": "running"}
    ]
    db.insert_process_snapshots(ts, procs)

    fetched = db.get_recent_process_snapshots(ts)
    assert len(fetched) == 2
    assert fetched[0]["process_name"] == "rustc.exe"  # ordered by cpu desc

    # Insight upsert
    ins = {
        "id": "cpu_test",
        "created_at": ts,
        "updated_at": ts,
        "resource": "CPU",
        "severity": "critical",
        "title": "CPU Stress",
        "observed_value": "95%",
        "rule_triggered": "Exceeds 90%",
        "explanation": "High compute",
        "evidence_json": "{}",
        "possible_cause": "rustc",
        "confidence_label": "High",
        "recommendation": "Wait for compile",
        "status": "ongoing",
        "resolved_at": None
    }
    db.upsert_insight(ins)
    active = db.get_active_insights()
    assert len(active) == 1
    assert active[0]["title"] == "CPU Stress"


def test_settings_persistence(tmp_path: Path):
    db_file = tmp_path / "test_settings.db"
    db = DatabaseManager(db_file)

    db.set_setting("theme", "dark_navy")
    db.set_setting("interval", "2.5")

    assert db.get_setting("theme") == "dark_navy"
    assert db.get_setting("interval") == "2.5"
    assert db.get_setting("missing_key", "default_val") == "default_val"


def test_clear_all_history(tmp_path: Path):
    db_file = tmp_path / "test_purge.db"
    db = DatabaseManager(db_file)

    metric = {
        "timestamp": "2026-10-10T12:00:00Z",
        "cpu_percent": 20.0, "cpu_frequency": None, "ram_percent": 30.0,
        "ram_used_bytes": 1, "ram_available_bytes": 1, "ram_total_bytes": 2,
        "disk_used_bytes": 1, "disk_free_bytes": 1, "disk_total_bytes": 2,
        "disk_percent": 50.0, "disk_read_bytes": 0, "disk_write_bytes": 0,
        "battery_percent": None, "battery_plugged": None, "health_score": 100.0
    }
    db.insert_system_metric(metric)
    assert len(db.get_recent_metrics()) == 1

    db.clear_all_history()
    assert len(db.get_recent_metrics()) == 0
