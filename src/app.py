"""
Application Core Controller and Monitoring Orchestrator.
Coordinates the background monitoring worker, database persistence,
analysis engines, and Qt signals for thread-safe UI updates.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal, QThread

from src.config import MonitorSettings, DEFAULT_DB_PATH
from src.database.db_manager import DatabaseManager
from src.monitoring.system_monitor import SystemMonitor, SystemReading
from src.monitoring.process_monitor import ProcessMonitor, ProcessInfo
from src.monitoring.platform_info import get_platform_info, PlatformInfo
from src.analysis.interpretation_engine import InterpretationEngine, Insight
from src.analysis.health_score import HealthScoreCalculator, HealthScoreResult
from src.analysis.recommendation_engine import RecommendationEngine, Recommendation
from src.alerts.alert_manager import AlertManager, AlertItem
from src.history.history_service import HistoryService

logger = logging.getLogger("HealthMonitor.AppController")


class MonitorWorker(QThread):
    """
    Dedicated background worker thread for capturing system metrics,
    evaluating interpretation rules, and storing historical records.
    """
    reading_ready = Signal(object)        # SystemReading
    score_ready = Signal(object)          # HealthScoreResult
    processes_ready = Signal(list)        # List[ProcessInfo]
    insights_ready = Signal(list)         # List[Insight]
    recommendations_ready = Signal(list)  # List[Recommendation]
    alerts_ready = Signal(list)           # List[AlertItem]
    status_changed = Signal(str)          # "running", "paused", "stopped"

    def __init__(
        self,
        system_monitor: SystemMonitor,
        process_monitor: ProcessMonitor,
        interpretation_engine: InterpretationEngine,
        alert_manager: AlertManager,
        db_manager: DatabaseManager,
        settings: MonitorSettings
    ):
        super().__init__()
        self.sys_mon = system_monitor
        self.proc_mon = process_monitor
        self.engine = interpretation_engine
        self.alert_mgr = alert_manager
        self.db = db_manager
        self.settings = settings

        self._is_running = False
        self._is_paused = False
        self._process_poll_counter = 0

    def run(self):
        self._is_running = True
        self.status_changed.emit("running")
        logger.info("MonitorWorker background thread started.")

        while self._is_running:
            if not self._is_paused:
                try:
                    # 1. Capture system hardware reading
                    reading: SystemReading = self.sys_mon.capture_reading()

                    # 2. Capture processes (every sample or every other sample for efficiency)
                    self._process_poll_counter += 1
                    all_processes: List[ProcessInfo] = self.proc_mon.capture_processes(limit=150)
                    top_cpu = self.proc_mon.get_top_cpu_processes(5, all_processes)

                    # 3. Compute Health Score
                    score_res: HealthScoreResult = HealthScoreCalculator.calculate(reading, self.settings)

                    # 4. Run the Interpretation Layer
                    insights: List[Insight] = self.engine.analyze(reading, top_cpu)

                    # 5. Generate Actionable Recommendations
                    recs: List[Recommendation] = RecommendationEngine.generate_recommendations(
                        self.engine.get_currently_active_insights()
                    )

                    # 6. Evaluate and Deduplicate Alerts
                    new_alerts: List[AlertItem] = self.alert_mgr.process_insights(insights)

                    # 7. Persist metrics and active insights to SQLite
                    metric_dict = {
                        "timestamp": reading.timestamp,
                        "cpu_percent": reading.cpu_percent,
                        "cpu_frequency": reading.cpu_frequency_mhz,
                        "ram_percent": reading.ram_percent,
                        "ram_used_bytes": reading.ram_used_bytes,
                        "ram_available_bytes": reading.ram_available_bytes,
                        "ram_total_bytes": reading.ram_total_bytes,
                        "disk_used_bytes": reading.disk_used_bytes,
                        "disk_free_bytes": reading.disk_free_bytes,
                        "disk_total_bytes": reading.disk_total_bytes,
                        "disk_percent": reading.disk_percent,
                        "disk_read_bytes": int(reading.disk_read_bytes_sec),
                        "disk_write_bytes": int(reading.disk_write_bytes_sec),
                        "battery_percent": reading.battery_percent,
                        "battery_plugged": 1 if reading.battery_plugged else (0 if reading.battery_plugged is False else None),
                        "health_score": score_res.score
                    }
                    self.db.insert_system_metric(metric_dict)

                    for ins in insights:
                        self.db.upsert_insight(ins.to_dict())

                    # Persist top 10 processes periodically
                    if self._process_poll_counter % 3 == 0:
                        top_to_store = sorted(all_processes, key=lambda p: p.cpu_percent, reverse=True)[:10]
                        self.db.insert_process_snapshots(
                            reading.timestamp,
                            [p.to_dict() for p in top_to_store]
                        )

                    # 8. Emit thread-safe signals to GUI
                    self.reading_ready.emit(reading)
                    self.score_ready.emit(score_res)
                    self.processes_ready.emit(all_processes)
                    self.insights_ready.emit(self.engine.get_currently_active_insights())
                    self.recommendations_ready.emit(recs)
                    if new_alerts:
                        self.alerts_ready.emit(new_alerts)

                except Exception as e:
                    logger.error(f"Error in monitoring loop cycle: {e}", exc_info=True)

            # Sleep in small increments for responsive pause/stop
            interval = max(0.5, self.settings.monitoring_interval_sec)
            elapsed = 0.0
            step = 0.2
            while self._is_running and elapsed < interval:
                self.msleep(int(step * 1000))
                elapsed += step

        self.status_changed.emit("stopped")
        logger.info("MonitorWorker background thread exited.")

    def pause(self):
        self._is_paused = True
        self.status_changed.emit("paused")

    def resume(self):
        self._is_paused = False
        self.status_changed.emit("running")

    def stop(self):
        self._is_running = False
        self.wait(2000)


class AppController(QObject):
    """Coordinates backend modules and UI interaction."""

    def __init__(self, settings: Optional[MonitorSettings] = None):
        super().__init__()
        self.settings = settings or MonitorSettings()
        
        # Core Services
        self.db = DatabaseManager(DEFAULT_DB_PATH)
        self.platform_info: PlatformInfo = get_platform_info()
        self.sys_mon = SystemMonitor()
        self.proc_mon = ProcessMonitor()
        self.engine = InterpretationEngine(self.settings)
        self.alert_mgr = AlertManager(self.db, self.settings)
        self.history_svc = HistoryService(self.db)
        
        # Background Thread
        self.worker: Optional[MonitorWorker] = None

    def start_monitoring(self):
        """Starts monitoring worker safely, avoiding duplicates."""
        if self.worker is not None and self.worker.isRunning():
            logger.warning("Monitoring worker is already active.")
            return

        self.worker = MonitorWorker(
            self.sys_mon,
            self.proc_mon,
            self.engine,
            self.alert_mgr,
            self.db,
            self.settings
        )
        self.worker.start()

    def pause_monitoring(self):
        if self.worker and self.worker.isRunning():
            self.worker.pause()

    def resume_monitoring(self):
        if self.worker and self.worker.isRunning():
            self.worker.resume()

    def stop_monitoring(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker = None

    def update_settings(self, new_settings: MonitorSettings):
        self.settings = new_settings
        self.engine.update_settings(new_settings)
        self.alert_mgr.update_settings(new_settings)
        if self.worker:
            self.worker.settings = new_settings
