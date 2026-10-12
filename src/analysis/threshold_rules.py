"""
Threshold evaluation rules for computer health monitoring.
Defines pure functions to evaluate resource states against configured thresholds.
"""

from typing import List, Optional, Tuple
from src.config import MonitorSettings


class ThresholdRules:
    """Evaluates individual resource metrics against configurable thresholds."""

    @staticmethod
    def evaluate_cpu(cpu_percent: float, settings: MonitorSettings) -> Tuple[str, str]:
        """
        Evaluate single CPU reading.
        Returns: (severity: 'normal'|'warning'|'critical', rule_description: str)
        """
        if cpu_percent >= settings.cpu_critical_pct:
            return "critical", f"CPU utilization ({cpu_percent:.1f}%) exceeds critical threshold ({settings.cpu_critical_pct:.1f}%)"
        elif cpu_percent >= settings.cpu_warning_pct:
            return "warning", f"CPU utilization ({cpu_percent:.1f}%) exceeds warning threshold ({settings.cpu_warning_pct:.1f}%)"
        return "normal", f"CPU utilization ({cpu_percent:.1f}%) is within normal operational limits"

    @staticmethod
    def is_cpu_sustained_high(
        recent_cpu_samples: List[float],
        settings: MonitorSettings
    ) -> Tuple[bool, str]:
        """
        Check if CPU utilization has been sustained above threshold for N samples.
        Prevents temporary spikes from generating false critical alarms.
        """
        required_samples = settings.sustained_samples
        if len(recent_cpu_samples) < required_samples:
            return False, f"Insufficient samples ({len(recent_cpu_samples)}/{required_samples}) to evaluate sustained load"

        window = recent_cpu_samples[-required_samples:]
        critical_count = sum(1 for val in window if val >= settings.cpu_critical_pct)
        warning_count = sum(1 for val in window if val >= settings.cpu_warning_pct)

        avg_val = sum(window) / len(window)

        if critical_count == required_samples:
            return True, f"Critical CPU load sustained for {required_samples} consecutive samples (avg: {avg_val:.1f}%)"
        if warning_count == required_samples:
            return True, f"Warning CPU load sustained for {required_samples} consecutive samples (avg: {avg_val:.1f}%)"

        return False, f"Recent CPU fluctuation (avg: {avg_val:.1f}%) without sustained threshold breach"

    @staticmethod
    def evaluate_ram(ram_percent: float, settings: MonitorSettings) -> Tuple[str, str]:
        """
        Evaluate RAM utilization.
        Returns: (severity: 'normal'|'warning'|'critical', rule_description: str)
        """
        if ram_percent >= settings.ram_critical_pct:
            return "critical", f"Memory utilization ({ram_percent:.1f}%) exceeds critical threshold ({settings.ram_critical_pct:.1f}%)"
        elif ram_percent >= settings.ram_warning_pct:
            return "warning", f"Memory utilization ({ram_percent:.1f}%) exceeds warning threshold ({settings.ram_warning_pct:.1f}%)"
        return "normal", f"Memory utilization ({ram_percent:.1f}%) is within normal limits"

    @staticmethod
    def evaluate_disk_space(disk_percent: float, settings: MonitorSettings) -> Tuple[str, str]:
        """
        Evaluate storage capacity.
        Returns: (severity: 'normal'|'warning'|'critical', rule_description: str)
        """
        if disk_percent >= settings.disk_critical_pct:
            return "critical", f"Disk capacity utilized ({disk_percent:.1f}%) exceeds critical limit ({settings.disk_critical_pct:.1f}%)"
        elif disk_percent >= settings.disk_warning_pct:
            return "warning", f"Disk capacity utilized ({disk_percent:.1f}%) exceeds warning limit ({settings.disk_warning_pct:.1f}%)"
        return "normal", f"Disk capacity utilized ({disk_percent:.1f}%) is within safe storage limits"

    @staticmethod
    def evaluate_battery(
        battery_available: bool,
        battery_percent: Optional[float],
        battery_plugged: Optional[bool],
        settings: MonitorSettings
    ) -> Tuple[str, str]:
        """
        Evaluate battery charge state.
        Returns: (severity: 'normal'|'warning'|'critical', rule_description: str)
        """
        if not battery_available or battery_percent is None:
            return "normal", "Battery sensor not present on this hardware (e.g. desktop system or VM)"

        if battery_plugged:
            return "normal", f"System connected to AC power (battery at {battery_percent:.1f}%)"

        if battery_percent <= settings.battery_critical_pct:
            return "critical", f"Battery charge critically low ({battery_percent:.1f}% <= {settings.battery_critical_pct:.1f}%) while on battery power"
        elif battery_percent <= settings.battery_warning_pct:
            return "warning", f"Battery charge low ({battery_percent:.1f}% <= {settings.battery_warning_pct:.1f}%) while on battery power"

        return "normal", f"Battery charge ({battery_percent:.1f}%) is adequate"
