"""
Platform and hardware detection module.
Inspects operating system, CPU architecture, core counts, memory size, and sensor support.
"""

import platform
import psutil
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class PlatformInfo:
    os_name: str
    os_release: str
    os_version: str
    architecture: str
    processor_name: str
    physical_cores: int
    logical_cores: int
    total_ram_bytes: int
    has_battery: bool
    partitions: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "os_name": self.os_name,
            "os_release": self.os_release,
            "os_version": self.os_version,
            "architecture": self.architecture,
            "processor_name": self.processor_name,
            "physical_cores": self.physical_cores,
            "logical_cores": self.logical_cores,
            "total_ram_bytes": self.total_ram_bytes,
            "has_battery": self.has_battery,
            "partitions": self.partitions
        }


def get_platform_info() -> PlatformInfo:
    """Safely inspects platform details with fallback values on permission or OS error."""
    try:
        physical_cores = psutil.cpu_count(logical=False) or 1
    except Exception:
        physical_cores = 1

    try:
        logical_cores = psutil.cpu_count(logical=True) or physical_cores
    except Exception:
        logical_cores = physical_cores

    try:
        vm = psutil.virtual_memory()
        total_ram = vm.total
    except Exception:
        total_ram = 0

    has_battery = False
    try:
        battery = psutil.sensors_battery()
        has_battery = (battery is not None)
    except Exception:
        has_battery = False

    partitions_info = []
    try:
        for part in psutil.disk_partitions(all=False):
            partitions_info.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "opts": part.opts
            })
    except Exception:
        pass

    return PlatformInfo(
        os_name=platform.system(),
        os_release=platform.release(),
        os_version=platform.version(),
        architecture=platform.machine(),
        processor_name=platform.processor() or "Unknown CPU",
        physical_cores=physical_cores,
        logical_cores=logical_cores,
        total_ram_bytes=total_ram,
        has_battery=has_battery,
        partitions=partitions_info
    )
