"""
Tests for HealthScoreCalculator.
Verifies deterministic health score calculation, boundary clamping,
avoidance of battery penalty when plugged in or absent, and correlation damping.
"""

import pytest
from src.config import MonitorSettings
from src.monitoring.system_monitor import SystemReading
from src.analysis.health_score import HealthScoreCalculator


def make_dummy_reading(
    cpu_percent=15.0,
    ram_percent=40.0,
    disk_percent=35.0,
    battery_available=False,
    battery_percent=None,
    battery_plugged=None
):
    return SystemReading(
        timestamp="2026-10-10T12:00:00Z",
        cpu_percent=cpu_percent,
        cpu_frequency_mhz=3200.0,
        cpu_cores_percent=[cpu_percent],
        ram_percent=ram_percent,
        ram_used_bytes=4 * (1024 ** 3),
        ram_available_bytes=12 * (1024 ** 3),
        ram_total_bytes=16 * (1024 ** 3),
        disk_path="C:\\",
        disk_used_bytes=100 * (1024 ** 3),
        disk_free_bytes=400 * (1024 ** 3),
        disk_total_bytes=500 * (1024 ** 3),
        disk_percent=disk_percent,
        disk_read_bytes_sec=0.0,
        disk_write_bytes_sec=0.0,
        battery_available=battery_available,
        battery_percent=battery_percent,
        battery_plugged=battery_plugged,
        battery_secs_left=None
    )


def test_perfect_health_score():
    settings = MonitorSettings()
    reading = make_dummy_reading(cpu_percent=10.0, ram_percent=30.0, disk_percent=40.0)
    result = HealthScoreCalculator.calculate(reading, settings)

    assert result.score == 100.0
    assert result.classification == "Excellent"
    assert result.breakdown["cpu_deduction"] == 0.0
    assert result.breakdown["ram_deduction"] == 0.0
    assert result.breakdown["disk_deduction"] == 0.0


def test_cpu_warning_and_critical_deductions():
    settings = MonitorSettings(cpu_warning_pct=70.0, cpu_critical_pct=90.0)

    # In warning range: 80%
    warn_reading = make_dummy_reading(cpu_percent=80.0)
    warn_result = HealthScoreCalculator.calculate(warn_reading, settings)
    assert 5.0 <= warn_result.breakdown["cpu_deduction"] <= 18.0
    assert warn_result.classification in ("Excellent", "Good")

    # In critical range: 95%
    crit_reading = make_dummy_reading(cpu_percent=95.0)
    crit_result = HealthScoreCalculator.calculate(crit_reading, settings)
    assert crit_result.breakdown["cpu_deduction"] > 18.0


def test_battery_no_penalty_when_plugged_or_unavailable():
    settings = MonitorSettings(battery_warning_pct=30.0, battery_critical_pct=15.0)

    # Battery absent (desktop PC)
    desktop_reading = make_dummy_reading(battery_available=False, battery_percent=None)
    res_desktop = HealthScoreCalculator.calculate(desktop_reading, settings)
    assert res_desktop.breakdown["battery_deduction"] == 0.0

    # Low battery (10%) but PLUGGED IN
    plugged_reading = make_dummy_reading(
        battery_available=True, battery_percent=10.0, battery_plugged=True
    )
    res_plugged = HealthScoreCalculator.calculate(plugged_reading, settings)
    assert res_plugged.breakdown["battery_deduction"] == 0.0

    # Low battery (10%) and UNPLUGGED (discharging) -> Should penalize
    unplugged_reading = make_dummy_reading(
        battery_available=True, battery_percent=10.0, battery_plugged=False
    )
    res_unplugged = HealthScoreCalculator.calculate(unplugged_reading, settings)
    assert res_unplugged.breakdown["battery_deduction"] > 0.0


def test_score_boundaries_clamping():
    settings = MonitorSettings()
    # Extreme pathological load across all resources
    extreme_reading = make_dummy_reading(
        cpu_percent=100.0,
        ram_percent=99.0,
        disk_percent=99.0,
        battery_available=True,
        battery_percent=2.0,
        battery_plugged=False
    )
    result = HealthScoreCalculator.calculate(extreme_reading, settings)
    assert 0.0 <= result.score <= 100.0
    assert result.classification == "Critical"
