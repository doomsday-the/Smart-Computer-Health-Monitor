"""
Tests for InterpretationEngine and ThresholdRules.
Validates the core research contribution: converting empirical OS metrics into
evidence-backed explanations, suppressing brief spikes, and tracking state transitions.
"""

import pytest
from src.config import MonitorSettings
from src.monitoring.system_monitor import SystemReading
from src.monitoring.process_monitor import ProcessInfo
from src.analysis.interpretation_engine import InterpretationEngine


def create_reading(cpu=20.0, ram=45.0, disk=50.0, batt_pct=80.0, batt_plugged=True, batt_avail=True):
    return SystemReading(
        timestamp="2026-10-10T12:00:00Z",
        cpu_percent=cpu,
        cpu_frequency_mhz=3000.0,
        cpu_cores_percent=[cpu],
        ram_percent=ram,
        ram_used_bytes=int(ram * 1024 * 1024 * 100),
        ram_available_bytes=int((100 - ram) * 1024 * 1024 * 100),
        ram_total_bytes=100 * 1024 * 1024 * 100,
        disk_path="C:\\",
        disk_used_bytes=int(disk * 1024 * 1024 * 1000),
        disk_free_bytes=int((100 - disk) * 1024 * 1024 * 1000),
        disk_total_bytes=100 * 1024 * 1024 * 1000,
        disk_percent=disk,
        disk_read_bytes_sec=1024.0,
        disk_write_bytes_sec=2048.0,
        battery_available=batt_avail,
        battery_percent=batt_pct if batt_avail else None,
        battery_plugged=batt_plugged if batt_avail else None,
        battery_secs_left=3600 if batt_avail else None
    )


def create_dummy_procs():
    return [
        ProcessInfo(pid=1001, name="python.exe", cpu_percent=88.5, memory_percent=12.0, memory_used_bytes=500*1024*1024, status="running", username="user"),
        ProcessInfo(pid=1002, name="browser.exe", cpu_percent=5.0, memory_percent=35.0, memory_used_bytes=1500*1024*1024, status="running", username="user"),
        ProcessInfo(pid=1003, name="svchost.exe", cpu_percent=1.0, memory_percent=2.0, memory_used_bytes=80*1024*1024, status="running", username="SYSTEM"),
    ]


def test_normal_metrics_generate_no_insights():
    settings = MonitorSettings(sustained_samples=3)
    engine = InterpretationEngine(settings)
    reading = create_reading(cpu=25.0, ram=50.0, disk=45.0)

    insights = engine.analyze(reading, create_dummy_procs())
    assert len(insights) == 0
    assert len(engine.get_currently_active_insights()) == 0


def test_brief_cpu_spike_does_not_trigger_sustained_alert():
    settings = MonitorSettings(sustained_samples=3, cpu_critical_pct=90.0)
    engine = InterpretationEngine(settings)

    # 1 normal reading
    engine.analyze(create_reading(cpu=20.0))
    # 1 spike reading at 95%
    insights = engine.analyze(create_reading(cpu=95.0), create_dummy_procs())
    # Should NOT trigger sustained CPU insight yet!
    cpu_insights = [i for i in insights if i.resource == "CPU"]
    assert len(cpu_insights) == 0

    # Next reading returns to normal
    insights_after = engine.analyze(create_reading(cpu=25.0))
    cpu_insights_after = [i for i in insights_after if i.resource == "CPU"]
    assert len(cpu_insights_after) == 0


def test_sustained_cpu_triggers_insight_with_evidence():
    settings = MonitorSettings(sustained_samples=3, cpu_critical_pct=90.0)
    engine = InterpretationEngine(settings)
    procs = create_dummy_procs()

    # Feed 3 consecutive critical readings
    engine.analyze(create_reading(cpu=92.0), procs)
    engine.analyze(create_reading(cpu=94.0), procs)
    insights = engine.analyze(create_reading(cpu=96.0), procs)

    cpu_insights = [i for i in insights if i.id == "cpu_sustained_pressure"]
    assert len(cpu_insights) == 1
    ins = cpu_insights[0]
    assert ins.severity == "critical"
    assert "Sustained" in ins.title
    assert "python.exe" in ins.possible_cause
    assert "evidence" in ins.__dict__
    assert len(ins.evidence["window_samples"]) == 3
    assert ins.status == "new"

    # Feed a 4th consecutive critical reading -> transitions to "ongoing"
    insights_next = engine.analyze(create_reading(cpu=95.0), procs)
    cpu_ins_next = [i for i in insights_next if i.id == "cpu_sustained_pressure"][0]
    assert cpu_ins_next.status == "ongoing"


def test_cpu_recovery_lifecycle():
    settings = MonitorSettings(sustained_samples=2, cpu_critical_pct=90.0)
    engine = InterpretationEngine(settings)

    # Trigger sustained load
    engine.analyze(create_reading(cpu=95.0))
    engine.analyze(create_reading(cpu=95.0))
    assert len(engine.get_currently_active_insights()) == 1

    # Load drops back to 20% -> Condition resolved
    insights_recovered = engine.analyze(create_reading(cpu=20.0))
    resolved_cpu = [i for i in insights_recovered if i.id == "cpu_sustained_pressure"]
    assert len(resolved_cpu) == 1
    assert resolved_cpu[0].status == "resolved"
    assert resolved_cpu[0].resolved_at is not None
    assert len(engine.get_currently_active_insights()) == 0


def test_ram_and_disk_insights():
    settings = MonitorSettings(ram_critical_pct=85.0, disk_critical_pct=90.0)
    engine = InterpretationEngine(settings)
    procs = create_dummy_procs()

    reading = create_reading(cpu=20.0, ram=92.0, disk=94.0)
    insights = engine.analyze(reading, procs)

    ram_ins = [i for i in insights if i.resource == "RAM"]
    disk_ins = [i for i in insights if i.resource == "Disk"]

    assert len(ram_ins) == 1
    assert ram_ins[0].severity == "critical"
    assert "High Memory Pressure" in ram_ins[0].title

    assert len(disk_ins) == 1
    assert disk_ins[0].severity == "critical"
    assert "Storage Exhaustion" in disk_ins[0].title


def test_combined_cpu_and_ram_condition():
    settings = MonitorSettings(sustained_samples=2, cpu_critical_pct=90.0, ram_critical_pct=85.0)
    engine = InterpretationEngine(settings)

    # First cycle
    engine.analyze(create_reading(cpu=95.0, ram=90.0))
    # Second cycle triggers sustained CPU and RAM concurrently
    insights = engine.analyze(create_reading(cpu=95.0, ram=90.0))

    combined_ins = [i for i in insights if i.id == "system_combined_stress"]
    assert len(combined_ins) == 1
    assert combined_ins[0].resource == "System"
    assert "Compounded System Workload" in combined_ins[0].title
