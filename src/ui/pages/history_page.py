"""
Performance History Page.
Visualizes long-term resource metrics stored in SQLite using an embedded Matplotlib canvas.
Supports 15m, 1h, 6h, 24h windows, statistical aggregations, and CSV export.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFrame, QGridLayout, QScrollArea, QFileDialog, QMessageBox
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from src.history.history_service import HistoryService, MetricSummary
from src.reports.report_exporter import ReportExporter


class HistoryPage(QWidget):
    """Historical telemetry graphs and statistical aggregations."""

    def __init__(self, history_service: HistoryService, parent=None):
        super().__init__(parent)
        self.history_svc = history_service
        self._current_records: List[Dict[str, Any]] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Performance History & Analysis")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #172033;")
        sub_lbl = QLabel("Analyze persistent telemetry trends, usage peaks, and health stability over time")
        sub_lbl.setStyleSheet("color: #667085; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Window Selector
        lbl_win = QLabel("Time Horizon:")
        lbl_win.setStyleSheet("color: #667085; font-weight: 600;")
        self.combo_window = QComboBox()
        self.combo_window.addItems(["Last 15 Minutes", "Last 1 Hour", "Last 6 Hours", "Last 24 Hours"])
        self.combo_window.setCurrentIndex(1)  # 1 Hour
        self.combo_window.currentIndexChanged.connect(self.refresh_history)
        header_row.addWidget(lbl_win)
        header_row.addWidget(self.combo_window)

        # Export CSV Button
        self.btn_export_csv = QPushButton("Export Window to CSV")
        self.btn_export_csv.setProperty("class", "btn-secondary")
        self.btn_export_csv.clicked.connect(self._export_csv)
        header_row.addWidget(self.btn_export_csv)

        main_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)

        # ---------------- Section 1: Summary Stats Cards ----------------
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(12)

        self.card_cpu_stat = self._create_stat_box("CPU Load", "Avg: -- | Peak: --")
        self.card_ram_stat = self._create_stat_box("RAM Allocation", "Avg: -- | Peak: --")
        self.card_score_stat = self._create_stat_box("Health Stability", "Avg: -- / 100")
        self.card_io_stat = self._create_stat_box("Disk I/O Peak", "Read: -- | Write: --")

        self.stats_grid.addWidget(self.card_cpu_stat, 0, 0)
        self.stats_grid.addWidget(self.card_ram_stat, 0, 1)
        self.stats_grid.addWidget(self.card_score_stat, 0, 2)
        self.stats_grid.addWidget(self.card_io_stat, 0, 3)
        self.content_layout.addLayout(self.stats_grid)

        # ---------------- Section 2: Embedded Matplotlib Charts ----------------
        chart_frame = QFrame()
        chart_frame.setProperty("class", "card-panel")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        # Matplotlib Figure with Dark Navy styling
        self.figure = Figure(figsize=(8, 6), facecolor="#FFFFFF")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(380)
        chart_layout.addWidget(self.canvas)

        self.content_layout.addWidget(chart_frame)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Initial plot
        self.refresh_history()

    def _create_stat_box(self, title: str, default_val: str) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "card-panel")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #667085; font-weight: 600; font-size: 11px;")
        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet("color: #172033; font-weight: 700; font-size: 13px;")
        v_lbl.setObjectName("val")
        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        return frame

    def refresh_history(self):
        """Query metrics for selected time window and redraw plot."""
        win_keys = ["15m", "1h", "6h", "24h"]
        idx = self.combo_window.currentIndex()
        key = win_keys[idx] if idx < len(win_keys) else "1h"

        self._current_records = self.history_svc.get_metrics_for_window(key)
        summary = self.history_svc.calculate_summary(self._current_records)

        # Update Stat Boxes
        if summary:
            self.card_cpu_stat.findChild(QLabel, "val").setText(
                f"Avg: {summary.avg_cpu}% | Peak: {summary.peak_cpu}%"
            )
            self.card_ram_stat.findChild(QLabel, "val").setText(
                f"Avg: {summary.avg_ram}% | Peak: {summary.peak_ram}%"
            )
            self.card_score_stat.findChild(QLabel, "val").setText(
                f"Avg: {summary.avg_health_score} (Min: {summary.min_health_score})"
            )
            self.card_io_stat.findChild(QLabel, "val").setText(
                f"R: {summary.peak_disk_read_kb / 1024:.1f} MB/s | W: {summary.peak_disk_write_kb / 1024:.1f} MB/s"
            )
        else:
            self.card_cpu_stat.findChild(QLabel, "val").setText("No data recorded yet")
            self.card_ram_stat.findChild(QLabel, "val").setText("No data recorded yet")
            self.card_score_stat.findChild(QLabel, "val").setText("No data recorded yet")
            self.card_io_stat.findChild(QLabel, "val").setText("No data recorded yet")

        # Redraw Matplotlib Axes
        self.figure.clear()

        ax1 = self.figure.add_subplot(2, 1, 1)
        ax2 = self.figure.add_subplot(2, 1, 2, sharex=ax1)

        # Apply dark styling to axes
        for ax in (ax1, ax2):
            ax.set_facecolor("#0F172A")
            ax.tick_params(colors="#667085")
            ax.grid(True, color="#172033", linestyle="--", alpha=0.6)
            for spine in ax.spines.values():
                spine.set_color("#E5EAF1")

        if not self._current_records:
            ax1.text(0.5, 0.5, "Collecting telemetry data... Continue monitoring to generate historical plots.",
                     color="#98A2B3", ha="center", va="center", transform=ax1.transAxes)
            self.canvas.draw()
            return

        timestamps = []
        cpu_vals = []
        ram_vals = []
        scores = []

        for r in self._current_records:
            ts_str = r.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                continue
            timestamps.append(dt)
            cpu_vals.append(float(r.get("cpu_percent", 0.0)))
            ram_vals.append(float(r.get("ram_percent", 0.0)))
            scores.append(float(r.get("health_score", 100.0)))

        if timestamps:
            # Subplot 1: CPU & RAM %
            ax1.plot(timestamps, cpu_vals, label="CPU %", color="#2563EB", linewidth=1.8)
            ax1.plot(timestamps, ram_vals, label="RAM %", color="#0891B2", linewidth=1.8)
            ax1.set_ylabel("Utilization (%)", color="#667085", fontsize=9)
            ax1.set_ylim(-2, 105)
            ax1.legend(facecolor="#FFFFFF", edgecolor="#172033", labelcolor="#172033", loc="upper left")

            # Subplot 2: Health Score (0-100)
            ax2.plot(timestamps, scores, label="Health Score", color="#16A34A", linewidth=2.0)
            ax2.axhline(80, color="#16A34A", linestyle=":", alpha=0.5, label="Excellent (>=80)")
            ax2.axhline(60, color="#D97706", linestyle=":", alpha=0.5, label="Warning (<60)")
            ax2.set_ylabel("Health Score", color="#667085", fontsize=9)
            ax2.set_ylim(-2, 105)
            ax2.legend(facecolor="#FFFFFF", edgecolor="#172033", labelcolor="#172033", loc="lower left")

            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            self.figure.autofmt_xdate()

        self.figure.tight_layout()
        self.canvas.draw()

    def _export_csv(self):
        """Export current filtered records to CSV file."""
        if not self._current_records:
            QMessageBox.warning(self, "No Data", "There are no historical records in the selected window to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Metrics CSV", "system_metrics_history.csv", "CSV Files (*.csv)"
        )
        if path:
            success = ReportExporter.export_metrics_to_csv(self._current_records, path)
            if success:
                QMessageBox.information(self, "Export Successful", f"Metrics successfully exported to:\n{path}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to save CSV file.")
