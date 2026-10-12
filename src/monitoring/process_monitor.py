"""
Process inspection and monitoring module.
Safely queries running operating-system processes, handles transient process lifecycles,
and extracts resource usage statistics for the interpretation engine and UI.
"""

import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import psutil

logger = logging.getLogger("HealthMonitor.ProcessMonitor")


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_used_bytes: int
    status: str
    username: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessMonitor:
    """Safely inspects processes on the system."""

    def __init__(self):
        # Prime process CPU percentages
        self._prime_processes()

    def _prime_processes(self) -> None:
        """Call cpu_percent once on processes to initialize measurement windows."""
        try:
            for p in psutil.process_iter(['pid']):
                try:
                    p.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            logger.debug(f"Process priming notice: {e}")

    def capture_processes(self, limit: int = 200) -> List[ProcessInfo]:
        """Capture currently active processes with their resource metrics."""
        results: List[ProcessInfo] = []
        attrs = ['pid', 'name', 'status']

        try:
            for proc in psutil.process_iter(attrs):
                try:
                    pinfo = proc.as_dict(attrs=attrs)
                    pid = pinfo.get('pid', 0)
                    name = pinfo.get('name') or f"PID {pid}"
                    status = pinfo.get('status') or "unknown"

                    # Fetch cpu and memory safely
                    try:
                        cpu_pct = float(proc.cpu_percent(interval=None) or 0.0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        cpu_pct = 0.0

                    try:
                        mem_pct = float(proc.memory_percent() or 0.0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        mem_pct = 0.0

                    try:
                        mem_info = proc.memory_info()
                        mem_bytes = int(mem_info.rss) if mem_info else 0
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        mem_bytes = 0

                    try:
                        user = proc.username()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                        user = "System/Protected"

                    results.append(ProcessInfo(
                        pid=pid,
                        name=name,
                        cpu_percent=cpu_pct,
                        memory_percent=mem_pct,
                        memory_used_bytes=mem_bytes,
                        status=status,
                        username=user
                    ))
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue
                except psutil.AccessDenied:
                    continue
                except Exception as e:
                    logger.debug(f"Transient error inspecting process: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error enumerating processes: {e}")

        return results

    def get_top_cpu_processes(self, count: int = 5, proc_list: Optional[List[ProcessInfo]] = None) -> List[ProcessInfo]:
        """Return the top CPU consuming processes."""
        procs = proc_list if proc_list is not None else self.capture_processes()
        return sorted(procs, key=lambda p: p.cpu_percent, reverse=True)[:count]

    def get_top_memory_processes(self, count: int = 5, proc_list: Optional[List[ProcessInfo]] = None) -> List[ProcessInfo]:
        """Return the top memory consuming processes."""
        procs = proc_list if proc_list is not None else self.capture_processes()
        return sorted(procs, key=lambda p: p.memory_used_bytes, reverse=True)[:count]
