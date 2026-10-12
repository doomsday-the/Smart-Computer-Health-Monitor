"""
The Interpretation Layer - Core Research Contribution.
Converts raw operating system resource metrics into explainable, evidence-based diagnoses.
Distinguishes between:
  1. Observed facts
  2. Operating system interpretation
  3. Possible contributing factors (without claiming correlation equals causation)
  4. Actionable next steps
Tracks condition persistence and state transitions (new -> ongoing -> resolved).
"""

import json
import logging
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.config import MonitorSettings
from src.monitoring.system_monitor import SystemReading
from src.monitoring.process_monitor import ProcessInfo
from src.analysis.threshold_rules import ThresholdRules

logger = logging.getLogger("HealthMonitor.InterpretationEngine")


@dataclass
class Insight:
    id: str
    resource: str  # CPU, RAM, Disk, Battery, System
    severity: str  # info, warning, critical
    title: str
    observed_value: str
    rule_triggered: str
    explanation: str
    evidence: Dict[str, Any]
    possible_cause: str
    confidence_label: str
    recommendation: str
    status: str  # new, ongoing, resolved
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_json"] = json.dumps(self.evidence)
        return d


class InterpretationEngine:
    """
    Intelligent system diagnosis engine.
    Analyzes streams of resource readings and process information to generate
    explainable insights with explicit evidence and state tracking.
    """

    def __init__(self, settings: MonitorSettings):
        self.settings = settings
        # History buffers for persistence evaluation
        self._cpu_history: deque[float] = deque(maxlen=60)
        self._ram_history: deque[float] = deque(maxlen=60)
        
        # State tracking for ongoing conditions
        # Key: insight_id -> Insight
        self._active_insights: Dict[str, Insight] = {}

    def update_settings(self, settings: MonitorSettings) -> None:
        self.settings = settings

    def analyze(
        self,
        reading: SystemReading,
        top_processes: Optional[List[ProcessInfo]] = None
    ) -> List[Insight]:
        """
        Analyze current reading and processes.
        Returns the list of currently active or newly resolved insights for this cycle.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        self._cpu_history.append(reading.cpu_percent)
        self._ram_history.append(reading.ram_percent)

        top_procs = top_processes or []
        top_cpu_procs = sorted(top_procs, key=lambda p: p.cpu_percent, reverse=True)[:3]
        top_mem_procs = sorted(top_procs, key=lambda p: p.memory_used_bytes, reverse=True)[:3]

        insights_this_cycle: List[Insight] = []
        active_keys_this_cycle: set[str] = set()

        # ----------------------------------------------------
        # 1. CPU Analysis: Sustained Load vs Spike
        # ----------------------------------------------------
        is_sustained, sustained_msg = ThresholdRules.is_cpu_sustained_high(
            list(self._cpu_history), self.settings
        )

        cpu_key = "cpu_sustained_pressure"
        if is_sustained:
            active_keys_this_cycle.add(cpu_key)
            severity = "critical" if reading.cpu_percent >= self.settings.cpu_critical_pct else "warning"
            
            top_cpu_str = ", ".join([f"{p.name} ({p.cpu_percent:.1f}%)" for p in top_cpu_procs]) or "N/A"
            procs_evidence = [
                {"name": p.name, "pid": p.pid, "cpu_percent": p.cpu_percent, "memory_mb": round(p.memory_used_bytes / (1024*1024), 1)}
                for p in top_cpu_procs
            ]

            evidence = {
                "current_cpu_percent": reading.cpu_percent,
                "window_samples": list(self._cpu_history)[-self.settings.sustained_samples:],
                "threshold_critical": self.settings.cpu_critical_pct,
                "threshold_warning": self.settings.cpu_warning_pct,
                "top_cpu_processes": procs_evidence,
                "cpu_frequency_mhz": reading.cpu_frequency_mhz
            }

            title = "Sustained High CPU Utilization" if severity == "critical" else "Elevated CPU Load"
            explanation = (
                f"Processor utilization has remained consistently high ({reading.cpu_percent:.1f}%) "
                f"across multiple evaluation cycles. When CPU demand approaches 100%, thread scheduling "
                f"queues grow, causing input latency and delayed application responsiveness."
            )
            possible_cause = (
                f"Top CPU-consuming processes ({top_cpu_str}) are actively executing compute-heavy tasks, "
                f"background indexing, compilation, or rendering. This reflects current workload demand, "
                f"not necessarily software malfunction."
            )
            recommendation = (
                "Review the listed high-CPU processes in the Process Explorer. "
                "Allow ongoing computational tasks to complete, or safely close unneeded background applications."
            )
            confidence = "High Confidence (Direct Metric)"

            insight = self._handle_insight_transition(
                key=cpu_key,
                resource="CPU",
                severity=severity,
                title=title,
                observed_value=f"{reading.cpu_percent:.1f}% (sustained {self.settings.sustained_samples} samples)",
                rule_triggered=sustained_msg,
                explanation=explanation,
                evidence=evidence,
                possible_cause=possible_cause,
                confidence_label=confidence,
                recommendation=recommendation,
                now_iso=now_iso
            )
            insights_this_cycle.append(insight)
        else:
            # Check if previous CPU condition has recovered
            resolved_insight = self._check_recovery(cpu_key, now_iso)
            if resolved_insight:
                insights_this_cycle.append(resolved_insight)

        # ----------------------------------------------------
        # 2. RAM Analysis: Memory Pressure & Page File Impact
        # ----------------------------------------------------
        ram_severity, ram_rule = ThresholdRules.evaluate_ram(reading.ram_percent, self.settings)
        ram_key = "ram_memory_pressure"
        if ram_severity in ("warning", "critical"):
            active_keys_this_cycle.add(ram_key)
            top_mem_str = ", ".join([
                f"{p.name} ({round(p.memory_used_bytes / (1024*1024), 1)} MB)"
                for p in top_mem_procs
            ]) or "N/A"

            procs_evidence = [
                {"name": p.name, "pid": p.pid, "memory_used_mb": round(p.memory_used_bytes / (1024*1024), 1), "memory_percent": p.memory_percent}
                for p in top_mem_procs
            ]

            avail_mb = round(reading.ram_available_bytes / (1024 * 1024), 1)
            total_mb = round(reading.ram_total_bytes / (1024 * 1024), 1)

            evidence = {
                "ram_percent": reading.ram_percent,
                "ram_available_mb": avail_mb,
                "ram_total_mb": total_mb,
                "top_memory_processes": procs_evidence,
                "threshold_critical": self.settings.ram_critical_pct,
                "threshold_warning": self.settings.ram_warning_pct
            }

            title = "High Memory Pressure Detected" if ram_severity == "critical" else "Elevated Memory Consumption"
            explanation = (
                f"RAM utilization is at {reading.ram_percent:.1f}%, leaving only {avail_mb} MB available out of {total_mb} MB. "
                f"When physical RAM is depleted, the operating system pages inactive memory blocks to disk swap/pagefile, "
                f"which can significantly degrade system responsiveness."
            )
            possible_cause = (
                f"Processes consuming large working sets ({top_mem_str}) may have extensive data loaded, "
                f"such as multiple browser tabs, virtual machines, or caching services. High RAM usage does not "
                f"by itself prove a memory leak."
            )
            recommendation = (
                "Review open browser tabs, background IDEs, or large datasets. "
                "Close memory-intensive applications that are not currently in use."
            )
            confidence = "High Confidence (Direct Metric)"

            insight = self._handle_insight_transition(
                key=ram_key,
                resource="RAM",
                severity=ram_severity,
                title=title,
                observed_value=f"{reading.ram_percent:.1f}% used ({avail_mb} MB free)",
                rule_triggered=ram_rule,
                explanation=explanation,
                evidence=evidence,
                possible_cause=possible_cause,
                confidence_label=confidence,
                recommendation=recommendation,
                now_iso=now_iso
            )
            insights_this_cycle.append(insight)
        else:
            resolved_insight = self._check_recovery(ram_key, now_iso)
            if resolved_insight:
                insights_this_cycle.append(resolved_insight)

        # ----------------------------------------------------
        # 3. Disk Storage Capacity Analysis
        # ----------------------------------------------------
        disk_severity, disk_rule = ThresholdRules.evaluate_disk_space(reading.disk_percent, self.settings)
        disk_key = "disk_storage_capacity"
        if disk_severity in ("warning", "critical"):
            active_keys_this_cycle.add(disk_key)
            free_gb = round(reading.disk_free_bytes / (1024 ** 3), 1)
            total_gb = round(reading.disk_total_bytes / (1024 ** 3), 1)

            evidence = {
                "mount_path": reading.disk_path,
                "disk_percent": reading.disk_percent,
                "free_gb": free_gb,
                "total_gb": total_gb,
                "threshold_critical": self.settings.disk_critical_pct,
                "threshold_warning": self.settings.disk_warning_pct
            }

            title = "Critical Storage Exhaustion" if disk_severity == "critical" else "Low Disk Storage Warning"
            explanation = (
                f"Target storage volume ({reading.disk_path}) is {reading.disk_percent:.1f}% full, "
                f"with only {free_gb} GB remaining. Operating systems require free disk space for temporary files, "
                f"virtual memory paging, system updates, and application crash dumps."
            )
            possible_cause = (
                "Accumulated software caches, downloads, system log archives, or large media files on the drive. "
                "Disk capacity exhaustion does not indicate hardware drive failure."
            )
            recommendation = (
                "Run Disk Cleanup or inspect user download folders and temporary caches. "
                "Relocate large inactive media or archive files to external or secondary storage."
            )
            confidence = "High Confidence (Direct Measurement)"

            insight = self._handle_insight_transition(
                key=disk_key,
                resource="Disk",
                severity=disk_severity,
                title=title,
                observed_value=f"{reading.disk_percent:.1f}% ({free_gb} GB free)",
                rule_triggered=disk_rule,
                explanation=explanation,
                evidence=evidence,
                possible_cause=possible_cause,
                confidence_label=confidence,
                recommendation=recommendation,
                now_iso=now_iso
            )
            insights_this_cycle.append(insight)
        else:
            resolved_insight = self._check_recovery(disk_key, now_iso)
            if resolved_insight:
                insights_this_cycle.append(resolved_insight)

        # ----------------------------------------------------
        # 4. Battery Level & Discharging Analysis
        # ----------------------------------------------------
        batt_severity, batt_rule = ThresholdRules.evaluate_battery(
            reading.battery_available, reading.battery_percent, reading.battery_plugged, self.settings
        )
        batt_key = "battery_charge_depletion"
        if batt_severity in ("warning", "critical"):
            active_keys_this_cycle.add(batt_key)
            evidence = {
                "battery_percent": reading.battery_percent,
                "battery_plugged": reading.battery_plugged,
                "battery_secs_left": reading.battery_secs_left,
                "threshold_critical": self.settings.battery_critical_pct,
                "threshold_warning": self.settings.battery_warning_pct
            }

            title = "Critically Low Battery Level" if batt_severity == "critical" else "Low Battery Charge"
            explanation = (
                f"Battery charge has fallen to {reading.battery_percent:.1f}% while running on battery power. "
                f"Operating system may trigger emergency hibernation or sudden power-off if battery drains completely."
            )
            possible_cause = (
                "Device is disconnected from AC mains power and current hardware workload has depleted charge."
            )
            recommendation = (
                "Connect the AC power adapter immediately or save ongoing documents and enable OS battery saver."
            )
            confidence = "High Confidence (Hardware Sensor)"

            insight = self._handle_insight_transition(
                key=batt_key,
                resource="Battery",
                severity=batt_severity,
                title=title,
                observed_value=f"{reading.battery_percent:.1f}% (unplugged)",
                rule_triggered=batt_rule,
                explanation=explanation,
                evidence=evidence,
                possible_cause=possible_cause,
                confidence_label=confidence,
                recommendation=recommendation,
                now_iso=now_iso
            )
            insights_this_cycle.append(insight)
        else:
            resolved_insight = self._check_recovery(batt_key, now_iso)
            if resolved_insight:
                insights_this_cycle.append(resolved_insight)

        # ----------------------------------------------------
        # 5. Combined Condition: Simultaneous CPU & RAM Stress
        # ----------------------------------------------------
        combined_key = "system_combined_stress"
        if (cpu_key in active_keys_this_cycle) and (ram_key in active_keys_this_cycle):
            active_keys_this_cycle.add(combined_key)
            evidence = {
                "cpu_percent": reading.cpu_percent,
                "ram_percent": reading.ram_percent,
                "top_cpu_processes": [p.name for p in top_cpu_procs],
                "top_ram_processes": [p.name for p in top_mem_procs]
            }
            title = "Compounded System Workload Pressure"
            explanation = (
                f"Both processor ({reading.cpu_percent:.1f}%) and memory ({reading.ram_percent:.1f}%) "
                f"are simultaneously under substantial pressure. This compounded state typically results in "
                f"noticeable desktop stutter, thrashing, and high response latency."
            )
            possible_cause = (
                "Heavy multi-tasking, concurrent compilation, or runaway resource contention among background services."
            )
            recommendation = (
                "Prioritize closing high-memory browser tabs and pausing background batch operations."
            )
            confidence = "Moderate Confidence (Joint Correlated Metrics)"

            insight = self._handle_insight_transition(
                key=combined_key,
                resource="System",
                severity="critical",
                title=title,
                observed_value=f"CPU: {reading.cpu_percent:.1f}%, RAM: {reading.ram_percent:.1f}%",
                rule_triggered="Simultaneous CPU and RAM threshold exceedance",
                explanation=explanation,
                evidence=evidence,
                possible_cause=possible_cause,
                confidence_label=confidence,
                recommendation=recommendation,
                now_iso=now_iso
            )
            insights_this_cycle.append(insight)
        else:
            resolved_insight = self._check_recovery(combined_key, now_iso)
            if resolved_insight:
                insights_this_cycle.append(resolved_insight)

        return insights_this_cycle

    def _handle_insight_transition(
        self,
        key: str,
        resource: str,
        severity: str,
        title: str,
        observed_value: str,
        rule_triggered: str,
        explanation: str,
        evidence: Dict[str, Any],
        possible_cause: str,
        confidence_label: str,
        recommendation: str,
        now_iso: str
    ) -> Insight:
        """Manages lifecycle: if already active -> 'ongoing'; if new -> 'new'."""
        if key in self._active_insights:
            existing = self._active_insights[key]
            existing.status = "ongoing"
            existing.severity = severity
            existing.updated_at = now_iso
            existing.observed_value = observed_value
            existing.evidence = evidence
            existing.explanation = explanation
            existing.possible_cause = possible_cause
            existing.recommendation = recommendation
            return existing
        else:
            new_insight = Insight(
                id=key,
                resource=resource,
                severity=severity,
                title=title,
                observed_value=observed_value,
                rule_triggered=rule_triggered,
                explanation=explanation,
                evidence=evidence,
                possible_cause=possible_cause,
                confidence_label=confidence_label,
                recommendation=recommendation,
                status="new",
                created_at=now_iso,
                updated_at=now_iso,
                resolved_at=None
            )
            self._active_insights[key] = new_insight
            return new_insight

    def _check_recovery(self, key: str, now_iso: str) -> Optional[Insight]:
        """Checks if an active insight should transition to 'resolved'."""
        if key in self._active_insights:
            resolved = self._active_insights.pop(key)
            resolved.status = "resolved"
            resolved.resolved_at = now_iso
            resolved.updated_at = now_iso
            resolved.explanation += f" (Condition resolved at {now_iso[:19].replace('T', ' ')})."
            return resolved
        return None

    def get_currently_active_insights(self) -> List[Insight]:
        """Returns all currently ongoing or active insights."""
        return list(self._active_insights.values())
