"""
Health Score calculation engine.
Calculates an explainable, deterministic 0-100 system health score based on real metrics.
Avoids unfair penalties when metrics are unavailable or when laptop is plugged in.
"""

from dataclasses import dataclass
from typing import Dict, Any
from src.config import MonitorSettings
from src.monitoring.system_monitor import SystemReading


@dataclass
class HealthScoreResult:
    score: float
    classification: str  # Excellent, Good, Warning, Critical
    explanation: str
    breakdown: Dict[str, float]  # Deductions per subsystem

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "classification": self.classification,
            "explanation": self.explanation,
            "breakdown": {k: round(v, 1) for k, v in self.breakdown.items()}
        }


class HealthScoreCalculator:
    """
    Computes a deterministic health score from 0 to 100.
    Documented mathematical formula:
      HealthScore = 100 - (CPU_deduction + RAM_deduction + Disk_deduction + Battery_deduction) * CorrelationDamper
    """

    @staticmethod
    def calculate(reading: SystemReading, settings: MonitorSettings) -> HealthScoreResult:
        base_score = 100.0
        breakdown: Dict[str, float] = {
            "cpu_deduction": 0.0,
            "ram_deduction": 0.0,
            "disk_deduction": 0.0,
            "battery_deduction": 0.0,
        }
        reasons = []

        # 1. CPU Deduction (up to 35 pts)
        cpu_val = reading.cpu_percent
        if cpu_val >= settings.cpu_critical_pct:
            # Scale from 18 to 35
            excess = (cpu_val - settings.cpu_critical_pct) / max(1.0, (100.0 - settings.cpu_critical_pct))
            deduction = 18.0 + (17.0 * min(1.0, excess))
            breakdown["cpu_deduction"] = deduction
            reasons.append(f"High CPU utilization ({cpu_val:.1f}%)")
        elif cpu_val >= settings.cpu_warning_pct:
            # Scale from 5 to 18
            ratio = (cpu_val - settings.cpu_warning_pct) / max(1.0, (settings.cpu_critical_pct - settings.cpu_warning_pct))
            deduction = 5.0 + (13.0 * min(1.0, ratio))
            breakdown["cpu_deduction"] = deduction
            reasons.append(f"Elevated CPU usage ({cpu_val:.1f}%)")

        # 2. RAM Deduction (up to 35 pts)
        ram_val = reading.ram_percent
        if ram_val >= settings.ram_critical_pct:
            excess = (ram_val - settings.ram_critical_pct) / max(1.0, (100.0 - settings.ram_critical_pct))
            deduction = 18.0 + (17.0 * min(1.0, excess))
            breakdown["ram_deduction"] = deduction
            reasons.append(f"High RAM pressure ({ram_val:.1f}%)")
        elif ram_val >= settings.ram_warning_pct:
            ratio = (ram_val - settings.ram_warning_pct) / max(1.0, (settings.ram_critical_pct - settings.ram_warning_pct))
            deduction = 5.0 + (13.0 * min(1.0, ratio))
            breakdown["ram_deduction"] = deduction
            reasons.append(f"Elevated RAM usage ({ram_val:.1f}%)")

        # 3. Disk Storage Deduction (up to 20 pts)
        disk_val = reading.disk_percent
        if disk_val >= settings.disk_critical_pct:
            excess = (disk_val - settings.disk_critical_pct) / max(1.0, (100.0 - settings.disk_critical_pct))
            deduction = 12.0 + (8.0 * min(1.0, excess))
            breakdown["disk_deduction"] = deduction
            reasons.append(f"Low free disk capacity ({disk_val:.1f}% used)")
        elif disk_val >= settings.disk_warning_pct:
            ratio = (disk_val - settings.disk_warning_pct) / max(1.0, (settings.disk_critical_pct - settings.disk_warning_pct))
            deduction = 4.0 + (8.0 * min(1.0, ratio))
            breakdown["disk_deduction"] = deduction
            reasons.append(f"Disk storage warning ({disk_val:.1f}% used)")

        # 4. Battery Deduction (up to 10 pts)
        # Note: ONLY penalize if battery is present AND discharging below threshold
        if reading.battery_available and reading.battery_percent is not None:
            if not reading.battery_plugged:
                batt_val = reading.battery_percent
                if batt_val <= settings.battery_critical_pct:
                    deduction = 10.0
                    breakdown["battery_deduction"] = deduction
                    reasons.append(f"Battery critically low ({batt_val:.1f}% unplugged)")
                elif batt_val <= settings.battery_warning_pct:
                    ratio = (settings.battery_warning_pct - batt_val) / max(1.0, (settings.battery_warning_pct - settings.battery_critical_pct))
                    deduction = 3.0 + (4.0 * min(1.0, ratio))
                    breakdown["battery_deduction"] = deduction
                    reasons.append(f"Battery low ({batt_val:.1f}% unplugged)")

        # Correlation damper: if both CPU and RAM are heavily penalized simultaneously,
        # apply a 0.85 damper to avoid double-penalizing correlated application stress
        total_deduction = sum(breakdown.values())
        if breakdown["cpu_deduction"] > 10.0 and breakdown["ram_deduction"] > 10.0:
            total_deduction *= 0.85

        final_score = max(0.0, min(100.0, base_score - total_deduction))

        if final_score >= 80.0:
            classification = "Excellent"
            explanation = "System resources are operating efficiently within healthy parameters." if not reasons else f"Overall healthy with minor notice: {', '.join(reasons)}."
        elif final_score >= 60.0:
            classification = "Good"
            explanation = f"Moderate load detected: {', '.join(reasons)}."
        elif final_score >= 40.0:
            classification = "Warning"
            explanation = f"Substantial resource strain: {', '.join(reasons)}. Investigation recommended."
        else:
            classification = "Critical"
            explanation = f"Critical performance pressure detected: {', '.join(reasons)}. Immediate attention advised."

        return HealthScoreResult(
            score=final_score,
            classification=classification,
            explanation=explanation,
            breakdown=breakdown
        )
