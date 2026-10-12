"""
Tests for MonitorSettings validation and ReportExporter.
Validates setting sanity checks, CSV generation, and ReportLab PDF compilation.
"""

from pathlib import Path
from src.config import MonitorSettings
from src.reports.report_exporter import ReportExporter
from src.history.history_service import HistoryService
from src.database.db_manager import DatabaseManager


def test_monitor_settings_validation():
    # Valid default settings
    valid_cfg = MonitorSettings()
    is_valid, _ = valid_cfg.validate()
    assert is_valid is True

    # Invalid: warning >= critical
    inv_cpu = MonitorSettings(cpu_warning_pct=95.0, cpu_critical_pct=90.0)
    ok, msg = inv_cpu.validate()
    assert ok is False
    assert "CPU warning threshold must be less" in msg

    # Invalid: negative interval
    inv_int = MonitorSettings(monitoring_interval_sec=-2.0)
    ok, msg = inv_int.validate()
    assert ok is False
    assert "Monitoring interval must be between" in msg

    # Invalid: battery critical > warning
    inv_batt = MonitorSettings(battery_critical_pct=40.0, battery_warning_pct=20.0)
    ok, msg = inv_batt.validate()
    assert ok is False
    assert "Battery critical threshold must be less" in msg


def test_empty_history_handling(tmp_path: Path):
    db_file = tmp_path / "empty.db"
    db = DatabaseManager(db_file)
    svc = HistoryService(db)

    records = svc.get_metrics_for_window("1h")
    assert len(records) == 0

    summary = svc.calculate_summary(records)
    assert summary is None


def test_csv_and_pdf_report_generation(tmp_path: Path):
    metrics = [
        {
            "id": 1,
            "timestamp": "2026-10-10T12:00:00Z",
            "cpu_percent": 35.0,
            "ram_percent": 55.0,
            "disk_percent": 60.0,
            "health_score": 95.0
        }
    ]
    alerts = [
        {
            "id": 1,
            "insight_id": "cpu_1",
            "timestamp": "2026-10-10T12:00:00Z",
            "severity": "warning",
            "resource": "CPU",
            "message": "Elevated CPU",
            "acknowledged": 1,
            "resolved": 0
        }
    ]

    csv_path = tmp_path / "test_out.csv"
    assert ReportExporter.export_metrics_to_csv(metrics, csv_path) is True
    assert csv_path.exists()
    assert "cpu_percent" in csv_path.read_text()

    pdf_path = tmp_path / "test_health_report.pdf"
    summary = {
        "count": 1,
        "avg_cpu": 35.0,
        "peak_cpu": 35.0,
        "avg_ram": 55.0,
        "peak_ram": 55.0,
        "avg_health_score": 95.0,
        "min_health_score": 95.0
    }
    insights = [
        {
            "id": "cpu_1",
            "resource": "CPU",
            "severity": "warning",
            "title": "Elevated CPU",
            "observed_value": "35%",
            "explanation": "Normal load test",
            "possible_cause": "Test",
            "recommendation": "None",
            "status": "ongoing"
        }
    ]
    recs = [
        {
            "id": "rec_1",
            "priority": "Medium",
            "title": "Test Rec",
            "reason": "Test reason",
            "expected_benefit": "Testing",
            "safety_note": "Safe"
        }
    ]

    success = ReportExporter.export_pdf_report(
        pdf_path, summary, metrics, insights, recs, alerts
    )
    assert success is True
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # valid PDF generated
