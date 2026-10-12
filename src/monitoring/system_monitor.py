"""
System resource monitoring module.
Collects real-time metrics for CPU, RAM, Disk, Disk I/O, and Battery using psutil.
Handles unsupported platforms, missing sensors, and permission errors gracefully.
"""

import logging
import os
import platform
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import psutil

logger = logging.getLogger("HealthMonitor.SystemMonitor")


@dataclass
class SystemReading:
    timestamp: str  # ISO 8601
    cpu_percent: float
    cpu_frequency_mhz: Optional[float]
    cpu_cores_percent: List[float]
    
    ram_percent: float
    ram_used_bytes: int
    ram_available_bytes: int
    ram_total_bytes: int
    
    disk_path: str
    disk_used_bytes: int
    disk_free_bytes: int
    disk_total_bytes: int
    disk_percent: float
    
    disk_read_bytes_sec: float
    disk_write_bytes_sec: float
    
    battery_available: bool
    battery_percent: Optional[float]
    battery_plugged: Optional[bool]
    battery_secs_left: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SystemMonitor:
    """Collects real-time computer resource utilization without blocking."""

    def __init__(self, target_disk_path: Optional[str] = None):
        if target_disk_path:
            self.target_disk_path = target_disk_path
        else:
            if platform.system() == "Windows":
                self.target_disk_path = os.getenv("SystemDrive", "C:") + "\\"
            else:
                self.target_disk_path = "/"

        # Prime CPU percent measurement
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception as e:
            logger.warning(f"Failed to prime CPU percent: {e}")

        self._last_disk_io: Optional[Any] = None
        self._last_disk_io_time: Optional[float] = None
        try:
            self._last_disk_io = psutil.disk_io_counters()
            self._last_disk_io_time = time.time()
        except Exception as e:
            logger.debug(f"Disk I/O counters unavailable: {e}")

    def capture_reading(self) -> SystemReading:
        """Capture a single complete system resource reading."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. CPU Metrics
        try:
            cpu_pct = float(psutil.cpu_percent(interval=None))
            cpu_cores = [float(p) for p in psutil.cpu_percent(interval=None, percpu=True)]
        except Exception as e:
            logger.error(f"Error reading CPU percent: {e}")
            cpu_pct = 0.0
            cpu_cores = []

        cpu_freq = None
        try:
            freq_info = psutil.cpu_freq()
            if freq_info:
                cpu_freq = float(freq_info.current)
        except Exception:
            cpu_freq = None

        # 2. RAM Metrics
        try:
            mem = psutil.virtual_memory()
            ram_pct = float(mem.percent)
            ram_used = int(mem.used)
            ram_avail = int(mem.available)
            ram_total = int(mem.total)
        except Exception as e:
            logger.error(f"Error reading RAM: {e}")
            ram_pct = 0.0
            ram_used = 0
            ram_avail = 0
            ram_total = 0

        # 3. Disk Capacity
        try:
            disk = psutil.disk_usage(self.target_disk_path)
            disk_used = int(disk.used)
            disk_free = int(disk.free)
            disk_total = int(disk.total)
            disk_pct = float(disk.percent)
        except Exception as e:
            logger.error(f"Error reading Disk usage for {self.target_disk_path}: {e}")
            disk_used = 0
            disk_free = 0
            disk_total = 0
            disk_pct = 0.0

        # 4. Disk I/O Activity
        read_rate = 0.0
        write_rate = 0.0
        current_time = time.time()
        try:
            current_io = psutil.disk_io_counters()
            if current_io and self._last_disk_io and self._last_disk_io_time:
                dt = current_time - self._last_disk_io_time
                if dt > 0.1:
                    read_delta = current_io.read_bytes - self._last_disk_io.read_bytes
                    write_delta = current_io.write_bytes - self._last_disk_io.write_bytes
                    read_rate = max(0.0, float(read_delta / dt))
                    write_rate = max(0.0, float(write_delta / dt))
            self._last_disk_io = current_io
            self._last_disk_io_time = current_time
        except Exception as e:
            logger.debug(f"Error reading Disk I/O: {e}")

        # 5. Battery Metrics
        battery_avail = False
        battery_pct = None
        battery_plugged = None
        battery_secs = None
        try:
            battery = psutil.sensors_battery()
            if battery is not None:
                battery_avail = True
                battery_pct = float(battery.percent)
                battery_plugged = bool(battery.power_plugged)
                battery_secs = int(battery.secsleft) if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft != psutil.POWER_TIME_UNKNOWN else None
        except Exception:
            battery_avail = False

        return SystemReading(
            timestamp=now_iso,
            cpu_percent=cpu_pct,
            cpu_frequency_mhz=cpu_freq,
            cpu_cores_percent=cpu_cores,
            ram_percent=ram_pct,
            ram_used_bytes=ram_used,
            ram_available_bytes=ram_avail,
            ram_total_bytes=ram_total,
            disk_path=self.target_disk_path,
            disk_used_bytes=disk_used,
            disk_free_bytes=disk_free,
            disk_total_bytes=disk_total,
            disk_percent=disk_pct,
            disk_read_bytes_sec=read_rate,
            disk_write_bytes_sec=write_rate,
            battery_available=battery_avail,
            battery_percent=battery_pct,
            battery_plugged=battery_plugged,
            battery_secs_left=battery_secs
        )
