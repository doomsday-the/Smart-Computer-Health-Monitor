"""
Tests for ProcessMonitor resilience.
Validates graceful handling of NoSuchProcess, AccessDenied, and ZombieProcess errors
when processes disappear or lack permissions during inspection.
"""

from unittest.mock import MagicMock, patch
import psutil
from src.monitoring.process_monitor import ProcessMonitor


def test_process_disappearing_during_inspection():
    pm = ProcessMonitor()

    # Create mock processes: one normal, one raising NoSuchProcess, one raising AccessDenied
    mock_p1 = MagicMock()
    mock_p1.as_dict.return_value = {"pid": 201, "name": "normal.exe", "status": "running"}
    mock_p1.cpu_percent.return_value = 15.0
    mock_p1.memory_percent.return_value = 5.0
    mock_mem = MagicMock()
    mock_mem.rss = 100 * 1024 * 1024
    mock_p1.memory_info.return_value = mock_mem
    mock_p1.username.return_value = "user"

    mock_p2 = MagicMock()
    mock_p2.as_dict.side_effect = psutil.NoSuchProcess(pid=202)

    mock_p3 = MagicMock()
    mock_p3.as_dict.return_value = {"pid": 203, "name": "protected.exe", "status": "running"}
    mock_p3.cpu_percent.side_effect = psutil.AccessDenied()
    mock_p3.memory_percent.side_effect = psutil.AccessDenied()
    mock_p3.memory_info.side_effect = psutil.AccessDenied()
    mock_p3.username.side_effect = psutil.AccessDenied()

    with patch("psutil.process_iter", return_value=[mock_p1, mock_p2, mock_p3]):
        results = pm.capture_processes()

        # Should handle without crashing and return captured info
        assert len(results) == 2  # p1 and p3 (with fallbacks)
        p1_res = [p for p in results if p.pid == 201][0]
        assert p1_res.name == "normal.exe"
        assert p1_res.cpu_percent == 15.0

        p3_res = [p for p in results if p.pid == 203][0]
        assert p3_res.cpu_percent == 0.0
        assert p3_res.username == "System/Protected"
