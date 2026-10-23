"""
Overview Dashboard Page.
Displays prominent health score, resource summary cards, active alerts,
recent activity log, and quick actions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QScrollArea
)

from src.ui.components.stat_card import StatCard
from src.ui.components.status_badge import StatusBadge
from src.monitoring.system_monitor import SystemReading
from src.analysis.health_score import HealthScoreResult
from src.analysis.interpretation_engine import Insight
from src.alerts.alert_manager import AlertItem


class OverviewPage(QWidget):
    """At-a-glance system health dashboard."""

    navigate_requested = Signal(int)  # Switch to page index
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header Title Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        page_title = QLabel("System Overview")
        page_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #172033;")
        page_subtitle = QLabel("Intelligent Operating-System Health & Interpretation Dashboard")
        page_subtitle.setStyleSheet("color: #667085; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Monitoring Control Buttons
        self.btn_pause_resume = QPushButton("Pause Monitoring")
        self.btn_pause_resume.setProperty("class", "btn-secondary")
        self.btn_export = QPushButton("Export Diagnostic Report")
        self.btn_export.setProperty("class", "btn-primary")
        self.btn_export.clicked.connect(lambda: self.export_requested.emit())
        header_row.addWidget(self.btn_pause_resume)
        header_row.addWidget(self.btn_export)
        main_layout.addLayout(header_row)

        # Scroll Area for responsive sizing
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # ---------------- Section A: Health Score Banner ----------------
        self.score_card = QFrame()
        self.score_card.setProperty("class", "card-panel")
        score_layout = QHBoxLayout(self.score_card)
        score_layout.setContentsMargins(20, 16, 20, 16)
        score_layout.setSpacing(20)

        # Left score circle / box
        left_score_box = QVBoxLayout()
        score_tag = QLabel("SYSTEM HEALTH SCORE")
        score_tag.setStyleSheet("color: #667085; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        self.score_num = QLabel("100")
        self.score_num.setStyleSheet("font-size: 48px; font-weight: 800; color: #16A34A;")
        left_score_box.addWidget(score_tag)
        left_score_box.addWidget(self.score_num)
        score_layout.addLayout(left_score_box)

        # Right score details
        right_score_box = QVBoxLayout()
        top_detail_row = QHBoxLayout()
        self.health_badge = StatusBadge("Excellent", "healthy")
        self.updated_lbl = QLabel("Awaiting initial telemetry...")
        self.updated_lbl.setStyleSheet("color: #98A2B3; font-size: 12px;")
        top_detail_row.addWidget(self.health_badge)
        top_detail_row.addStretch()
        top_detail_row.addWidget(self.updated_lbl)
        right_score_box.addLayout(top_detail_row)

        self.score_desc = QLabel(
            "System is operating efficiently. All primary operating system metrics "
            "(CPU, Memory, Storage, Power) are within healthy operational thresholds."
        )
        self.score_desc.setStyleSheet("color: #667085; font-size: 13px;")
        self.score_desc.setWordWrap(True)
        right_score_box.addWidget(self.score_desc)

        disclaimer = QLabel(
            "Note: This score is a research-defined heuristic combining CPU, memory, storage pressure, "
            "and battery state. It is not an official hardware benchmark."
        )
        disclaimer.setStyleSheet("color: #98A2B3; font-size: 11px; font-style: italic;")
        disclaimer.setWordWrap(True)
        right_score_box.addWidget(disclaimer)

        score_layout.addLayout(right_score_box, stretch=1)
        self.content_layout.addWidget(self.score_card)

        # ---------------- Section B: Resource Summary Cards Grid ----------------
        cards_grid = QGridLayout()
        cards_grid.setSpacing(14)

        # 1. CPU Card
        self.cpu_card = StatCard(title="CPU Utilization", unit="%", chart_color="#2563EB")
        cards_grid.addWidget(self.cpu_card, 0, 0)

        # 2. RAM Card
        self.ram_card = StatCard(title="RAM Memory Utilization", unit="%", chart_color="#0891B2")
        cards_grid.addWidget(self.ram_card, 0, 1)

        # 3. Disk Card
        self.disk_card = StatCard(title="System Drive Capacity", unit="%", chart_color="#D97706", has_chart=False)
        cards_grid.addWidget(self.disk_card, 1, 0)

        # 4. Battery / Power Card
        self.battery_card = StatCard(title="Power & Battery State", unit="%", chart_color="#16A34A", has_chart=False)
        cards_grid.addWidget(self.battery_card, 1, 1)

        self.content_layout.addLayout(cards_grid)

        # ---------------- Section C: Active Alerts & Quick Actions ----------------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(14)

        # Left: Active Alerts Panel
        self.alerts_panel = QFrame()
        self.alerts_panel.setProperty("class", "card-panel")
        alerts_layout = QVBoxLayout(self.alerts_panel)
        alerts_layout.setContentsMargins(16, 14, 16, 14)
        alerts_header = QHBoxLayout()
        alerts_title = QLabel("Active Alerts")
        alerts_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #172033;")
        view_all_alerts = QPushButton("View All Alerts →")
        view_all_alerts.setStyleSheet("background: transparent; color: #2563EB; border: none; font-weight: 600;")
        view_all_alerts.clicked.connect(lambda: self.navigate_requested.emit(4))  # Index 4: Alerts
        alerts_header.addWidget(alerts_title)
        alerts_header.addStretch()
        alerts_header.addWidget(view_all_alerts)
        alerts_layout.addLayout(alerts_header)

        self.alerts_list_layout = QVBoxLayout()
        self.lbl_no_alerts = QLabel("No active unresolved alerts. System status is normal.")
        self.lbl_no_alerts.setStyleSheet("color: #98A2B3; font-size: 12px; padding: 12px 0;")
        self.alerts_list_layout.addWidget(self.lbl_no_alerts)
        alerts_layout.addLayout(self.alerts_list_layout)
        bottom_row.addWidget(self.alerts_panel, stretch=2)

        # Right: Quick Navigation Actions
        actions_panel = QFrame()
        actions_panel.setProperty("class", "card-panel")
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(16, 14, 16, 14)
        act_title = QLabel("Quick Navigation")
        act_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #172033;")
        actions_layout.addWidget(act_title)

        btn_proc = QPushButton("Open Process Explorer")
        btn_proc.setProperty("class", "btn-secondary")
        btn_proc.clicked.connect(lambda: self.navigate_requested.emit(2))  # Index 2: Process Explorer
        actions_layout.addWidget(btn_proc)

        btn_insights = QPushButton("View Explainable Insights")
        btn_insights.setProperty("class", "btn-secondary")
        btn_insights.clicked.connect(lambda: self.navigate_requested.emit(3))  # Index 3: Insights
        actions_layout.addWidget(btn_insights)

        btn_recs = QPushButton("View Smart Recommendations")
        btn_recs.setProperty("class", "btn-secondary")
        btn_recs.clicked.connect(lambda: self.navigate_requested.emit(6))  # Index 6: Recommendations
        actions_layout.addWidget(btn_recs)

        btn_hist = QPushButton("Inspect Performance History")
        btn_hist.setProperty("class", "btn-secondary")
        btn_hist.clicked.connect(lambda: self.navigate_requested.emit(5))  # Index 5: History
        actions_layout.addWidget(btn_hist)

        actions_layout.addStretch()
        bottom_row.addWidget(actions_panel, stretch=1)

        self.content_layout.addLayout(bottom_row)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def update_telemetry(self, reading: SystemReading, score: HealthScoreResult):
        """Update dashboard with fresh telemetry reading and health score."""
        now_time = datetime.now().strftime("%H:%M:%S")
        self.updated_lbl.setText(f"Last updated: {now_time}")

        # Update Health Score
        score_val = score.score
        self.score_num.setText(f"{int(score_val)}")
        if score_val >= 80:
            self.score_num.setStyleSheet("font-size: 48px; font-weight: 800; color: #16A34A;")
            self.health_badge.set_severity("healthy", "Excellent")
        elif score_val >= 60:
            self.score_num.setStyleSheet("font-size: 48px; font-weight: 800; color: #0891B2;")
            self.health_badge.set_severity("good", "Good")
        elif score_val >= 40:
            self.score_num.setStyleSheet("font-size: 48px; font-weight: 800; color: #D97706;")
            self.health_badge.set_severity("warning", "Warning")
        else:
            self.score_num.setStyleSheet("font-size: 48px; font-weight: 800; color: #DC2626;")
            self.health_badge.set_severity("critical", "Critical")

        self.score_desc.setText(score.explanation)

        # Update CPU Card
        freq_str = f"{reading.cpu_frequency_mhz:.0f} MHz • " if reading.cpu_frequency_mhz else ""
        cores_str = f"{len(reading.cpu_cores_percent)} Cores" if reading.cpu_cores_percent else ""
        cpu_sev = "critical" if reading.cpu_percent >= 90 else ("warning" if reading.cpu_percent >= 70 else "healthy")
        cpu_interp = "Normal processor execution" if cpu_sev == "healthy" else ("Moderate processor demand" if cpu_sev == "warning" else "Severe CPU contention")
        self.cpu_card.update_metric(
            value=reading.cpu_percent,
            subtitle=f"{freq_str}{cores_str}",
            severity=cpu_sev,
            interpretation=cpu_interp
        )

        # Update RAM Card
        used_gb = reading.ram_used_bytes / (1024 ** 3)
        total_gb = reading.ram_total_bytes / (1024 ** 3)
        avail_gb = reading.ram_available_bytes / (1024 ** 3)
        ram_sev = "critical" if reading.ram_percent >= 85 else ("warning" if reading.ram_percent >= 70 else "healthy")
        ram_interp = f"{avail_gb:.1f} GB available memory"
        self.ram_card.update_metric(
            value=reading.ram_percent,
            subtitle=f"{used_gb:.1f} / {total_gb:.1f} GB",
            severity=ram_sev,
            interpretation=ram_interp
        )

        # Update Disk Card
        disk_used_gb = reading.disk_used_bytes / (1024 ** 3)
        disk_total_gb = reading.disk_total_bytes / (1024 ** 3)
        disk_free_gb = reading.disk_free_bytes / (1024 ** 3)
        disk_sev = "critical" if reading.disk_percent >= 90 else ("warning" if reading.disk_percent >= 70 else "healthy")
        io_read_mb = reading.disk_read_bytes_sec / (1024 * 1024)
        io_write_mb = reading.disk_write_bytes_sec / (1024 * 1024)
        self.disk_card.update_metric(
            value=reading.disk_percent,
            subtitle=f"{disk_used_gb:.1f} / {disk_total_gb:.1f} GB ({disk_free_gb:.1f} GB free)",
            severity=disk_sev,
            interpretation=f"Disk I/O rate: R: {io_read_mb:.1f} MB/s | W: {io_write_mb:.1f} MB/s (Capacity vs I/O distinguished)"
        )

        # Update Battery Card
        if reading.battery_available and reading.battery_percent is not None:
            plug_str = "Plugged In (Charging / AC)" if reading.battery_plugged else "Running on Battery"
            batt_sev = "healthy" if reading.battery_plugged else ("critical" if reading.battery_percent <= 15 else ("warning" if reading.battery_percent <= 30 else "healthy"))
            time_str = f" • ~{reading.battery_secs_left // 60}m left" if (reading.battery_secs_left and not reading.battery_plugged) else ""
            self.battery_card.update_metric(
                value=reading.battery_percent,
                value_text=f"{reading.battery_percent:.0f}%",
                subtitle=plug_str,
                severity=batt_sev,
                interpretation=f"Power Source: {plug_str}{time_str}"
            )
        else:
            self.battery_card.update_metric(
                value=0,
                value_text="N/A",
                subtitle="Not available on this device",
                severity="healthy",
                interpretation="Hardware has no battery sensor (e.g. desktop system or virtual machine)."
            )

    def update_active_alerts(self, alerts: List[Any]):
        """Render recent unresolved alerts in the dashboard."""
        # Clear previous items
        while self.alerts_list_layout.count():
            item = self.alerts_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not alerts:
            lbl = QLabel("No active unresolved alerts. System status is normal.")
            lbl.setStyleSheet("color: #98A2B3; font-size: 12px; padding: 12px 0;")
            self.alerts_list_layout.addWidget(lbl)
            return

        for a in alerts[:3]:
            row = QFrame()
            row.setStyleSheet("background-color: #F8FAFC; border-radius: 6px; padding: 8px 12px; margin-bottom: 4px;")
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(0, 0, 0, 0)
            
            sev = getattr(a, 'severity', None) or (a.get('severity') if isinstance(a, dict) else 'info')
            badge = StatusBadge(sev.capitalize(), sev)
            r_lay.addWidget(badge)

            msg = getattr(a, 'message', None) or (a.get('message') if isinstance(a, dict) else '')
            lbl = QLabel(msg)
            lbl.setStyleSheet("color: #344054; font-size: 12px;")
            lbl.setWordWrap(True)
            r_lay.addWidget(lbl, stretch=1)

            btn = QPushButton("Explain →")
            btn.setStyleSheet("background: transparent; color: #0891B2; border: none; font-weight: 600; font-size: 11px;")
            btn.clicked.connect(lambda: self.navigate_requested.emit(3))  # View Insights
            r_lay.addWidget(btn)

            self.alerts_list_layout.addWidget(row)
