"""
Main Application Window.
Coordinates persistent sidebar navigation, stacked pages, real-time telemetry wiring,
report export dialogs, and clean application shutdown.
"""

import logging
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QFileDialog, QMessageBox, QStatusBar
)

from src.app import AppController
from src.ui.pages.overview_page import OverviewPage
from src.ui.pages.resource_monitor_page import ResourceMonitorPage
from src.ui.pages.process_explorer_page import ProcessExplorerPage
from src.ui.pages.health_insights_page import HealthInsightsPage
from src.ui.pages.alerts_page import AlertsPage
from src.ui.pages.history_page import HistoryPage
from src.ui.pages.recommendations_page import RecommendationsPage
from src.ui.pages.settings_page import SettingsPage
from src.ui.pages.about_page import AboutPage
from src.reports.report_exporter import ReportExporter

logger = logging.getLogger("HealthMonitor.MainWindow")


class MainWindow(QMainWindow):
    """Primary desktop window hosting navigation and stacked pages."""

    def __init__(self, controller: AppController):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Smart Computer Health Monitor — Intelligent OS Diagnostic System")
        self.resize(1280, 840)
        self.setMinimumSize(1024, 680)

        # Central container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # ---------------- 1. Persistent Sidebar ----------------
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 16)
        sidebar_layout.setSpacing(4)

        # App Brand Header
        brand_box = QFrame()
        brand_box.setObjectName("sidebarHeader")
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(14, 16, 14, 16)
        app_title = QLabel("Health Monitor")
        app_title.setObjectName("appTitle")
        app_sub = QLabel("Intelligent OS Diagnostics")
        app_sub.setObjectName("appSubtitle")
        brand_layout.addWidget(app_title)
        brand_layout.addWidget(app_sub)
        sidebar_layout.addWidget(brand_box)

        # Navigation Buttons List
        self.nav_buttons = []
        nav_items = [
            ("📊 Overview", 0),
            ("⚡ Resource Monitor", 1),
            ("🔍 Process Explorer", 2),
            ("💡 Health Insights", 3),
            ("🔔 Alerts", 4),
            ("📈 Performance History", 5),
            ("🎯 Recommendations", 6),
            ("⚙️ Settings", 7),
            ("ℹ️ About Project", 8),
        ]

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Monitoring Status Widget in Sidebar
        status_box = QFrame()
        status_box.setStyleSheet("background-color: #162032; border-radius: 8px; margin: 0 10px; padding: 10px;")
        s_lay = QVBoxLayout(status_box)
        s_lay.setContentsMargins(0, 0, 0, 0)
        self.sidebar_mon_lbl = QLabel("● Monitoring Active")
        self.sidebar_mon_lbl.setStyleSheet("color: #22C55E; font-weight: 600; font-size: 11px;")
        self.sidebar_rate_lbl = QLabel(f"Interval: {self.controller.settings.monitoring_interval_sec}s")
        self.sidebar_rate_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        s_lay.addWidget(self.sidebar_mon_lbl)
        s_lay.addWidget(self.sidebar_rate_lbl)
        sidebar_layout.addWidget(status_box)

        main_h_layout.addWidget(self.sidebar)

        # ---------------- 2. Stacked Pages Area ----------------
        self.stack = QStackedWidget()

        # Instantiate Pages
        self.page_overview = OverviewPage()
        self.page_res_mon = ResourceMonitorPage()
        self.page_procs = ProcessExplorerPage()
        self.page_insights = HealthInsightsPage()
        self.page_alerts = AlertsPage(self.controller.alert_mgr, self.controller.db)
        self.page_history = HistoryPage(self.controller.history_svc)
        self.page_recs = RecommendationsPage()
        self.page_settings = SettingsPage(self.controller.settings, self.controller.db)
        self.page_about = AboutPage(self.controller.platform_info)

        self.stack.addWidget(self.page_overview)      # 0
        self.stack.addWidget(self.page_res_mon)       # 1
        self.stack.addWidget(self.page_procs)         # 2
        self.stack.addWidget(self.page_insights)      # 3
        self.stack.addWidget(self.page_alerts)        # 4
        self.stack.addWidget(self.page_history)       # 5
        self.stack.addWidget(self.page_recs)          # 6
        self.stack.addWidget(self.page_settings)      # 7
        self.stack.addWidget(self.page_about)         # 8

        main_h_layout.addWidget(self.stack, stretch=1)

        # Setup Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("background-color: #111827; color: #94A3B8; font-size: 11px;")
        self.status_bar.showMessage("Smart Computer Health Monitor loaded • Ready")

        # Wire Signals
        self._wire_signals()

        # Select first page (Overview)
        self.switch_page(0)

        # Auto-start monitoring if enabled
        if self.controller.settings.auto_start_monitoring:
            self.controller.start_monitoring()
            if self.controller.worker:
                self._connect_worker_signals(self.controller.worker)

    def switch_page(self, index: int):
        """Switch stacked page and update sidebar active state."""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            if i == index:
                btn.setProperty("class", "nav-btn active")
            else:
                btn.setProperty("class", "nav-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _wire_signals(self):
        # Overview Navigation Links
        self.page_overview.navigate_requested.connect(self.switch_page)
        self.page_overview.export_requested.connect(self._handle_pdf_export)

        # Controls
        self.page_overview.btn_pause_resume.clicked.connect(self._toggle_monitoring)

        # Resource monitor interval changed
        self.page_res_mon.interval_changed.connect(self._on_interval_changed)

        # Settings Updated
        self.page_settings.settings_updated.connect(self._on_settings_updated)

        # Worker Telemetry Signals (if worker exists)
        if self.controller.worker:
            self._connect_worker_signals(self.controller.worker)

    def _connect_worker_signals(self, worker):
        worker.reading_ready.connect(self._on_reading_ready)
        worker.score_ready.connect(self._on_score_ready)
        worker.processes_ready.connect(self.page_procs.update_processes)
        worker.insights_ready.connect(self.page_insights.update_insights)
        worker.recommendations_ready.connect(self.page_recs.update_recommendations)
        worker.alerts_ready.connect(self._on_alerts_ready)
        worker.status_changed.connect(self._on_status_changed)

    def _on_reading_ready(self, reading):
        self._last_reading = reading
        self.page_res_mon.update_telemetry(reading)
        # Update overview if score is also present
        if hasattr(self, '_last_score') and self._last_score:
            self.page_overview.update_telemetry(reading, self._last_score)

    def _on_score_ready(self, score):
        self._last_score = score
        if hasattr(self, '_last_reading') and self._last_reading:
            self.page_overview.update_telemetry(self._last_reading, score)

    def _on_alerts_ready(self, alerts):
        self.page_overview.update_active_alerts(alerts)
        self.page_alerts.refresh_alerts()

    def _on_status_changed(self, status: str):
        if status == "running":
            self.page_overview.btn_pause_resume.setText("Pause Monitoring")
            self.sidebar_mon_lbl.setText("● Monitoring Active")
            self.sidebar_mon_lbl.setStyleSheet("color: #22C55E; font-weight: 600; font-size: 11px;")
        elif status == "paused":
            self.page_overview.btn_pause_resume.setText("Resume Monitoring")
            self.sidebar_mon_lbl.setText("⏸ Monitoring Paused")
            self.sidebar_mon_lbl.setStyleSheet("color: #F59E0B; font-weight: 600; font-size: 11px;")
        elif status == "stopped":
            self.page_overview.btn_pause_resume.setText("Start Monitoring")
            self.sidebar_mon_lbl.setText("⏹ Monitoring Stopped")
            self.sidebar_mon_lbl.setStyleSheet("color: #EF4444; font-weight: 600; font-size: 11px;")

    def _toggle_monitoring(self):
        if not self.controller.worker or not self.controller.worker.isRunning():
            self.controller.start_monitoring()
            self._connect_worker_signals(self.controller.worker)
        elif self.controller.worker._is_paused:
            self.controller.resume_monitoring()
        else:
            self.controller.pause_monitoring()

    def _on_interval_changed(self, interval: float):
        self.controller.settings.monitoring_interval_sec = interval
        self.sidebar_rate_lbl.setText(f"Interval: {interval:.1f}s")
        self.controller.update_settings(self.controller.settings)

    def _on_settings_updated(self, new_settings):
        self.controller.update_settings(new_settings)
        self.sidebar_rate_lbl.setText(f"Interval: {new_settings.monitoring_interval_sec:.1f}s")

    def _handle_pdf_export(self):
        """Export comprehensive diagnostic PDF report."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Diagnostic PDF Report", "system_health_report.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return

        # Fetch data for report
        records = self.controller.history_svc.get_metrics_for_window("1h")
        summary = self.controller.history_svc.calculate_summary(records)
        active_insights = self.controller.db.get_active_insights()
        recs = [r.to_dict() for r in self.page_recs._current_recs]
        alerts = self.controller.db.get_alerts(only_active=False, limit=20)

        summary_dict = summary.__dict__ if summary else None

        success = ReportExporter.export_pdf_report(
            target_path=Path(path),
            summary_stats=summary_dict,
            recent_metrics=records,
            insights=active_insights,
            recommendations=recs,
            alerts=alerts
        )

        if success:
            QMessageBox.information(
                self, "Export Successful",
                f"Diagnostic Health Report successfully generated at:\n{path}"
            )
        else:
            QMessageBox.critical(self, "Export Error", "Failed to generate PDF report.")

    def closeEvent(self, event):
        """Safely terminate monitoring worker threads before exit."""
        logger.info("Application closing. Terminating monitoring worker thread safely.")
        self.controller.stop_monitoring()
        event.accept()
