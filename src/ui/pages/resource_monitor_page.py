"""
Resource Monitor Page.
In-depth real-time view of CPU (per-core breakdown), RAM, Disk Capacity vs Disk I/O activity,
and Battery state with configurable sample intervals.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QGridLayout, QScrollArea, QProgressBar
)
from src.ui.components.stat_card import StatCard
from src.ui.components.mini_chart import RealtimeSparkline
from src.monitoring.system_monitor import SystemReading


class ResourceMonitorPage(QWidget):
    """Detailed real-time multi-resource monitor."""

    interval_changed = Signal(float)
    navigate_insights_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header with interval selector
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Real-Time Resource Monitor")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #F8FAFC;")
        sub_lbl = QLabel("Continuous telemetry streaming across CPU cores, Memory allocations, and Storage I/O")
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Interval combo
        interval_box = QHBoxLayout()
        lbl_int = QLabel("Sampling Interval:")
        lbl_int.setStyleSheet("color: #94A3B8; font-weight: 600;")
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["1.0s (High Overhead)", "2.0s (Recommended)", "5.0s (Power Saver)", "10.0s (Low Overhead)"])
        self.combo_interval.setCurrentIndex(1)  # 2.0s default
        self.combo_interval.currentIndexChanged.connect(self._on_interval_selected)
        interval_box.addWidget(lbl_int)
        interval_box.addWidget(self.combo_interval)
        header_row.addLayout(interval_box)
        main_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # ---------------- Section 1: Detailed CPU & Core Grid ----------------
        cpu_panel = QFrame()
        cpu_panel.setProperty("class", "card-panel")
        cpu_layout = QVBoxLayout(cpu_panel)
        cpu_layout.setSpacing(12)

        cpu_header = QHBoxLayout()
        cpu_title = QLabel("Processor (CPU) & Core Telemetry")
        cpu_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F8FAFC;")
        self.cpu_total_lbl = QLabel("Total: 0.0%")
        self.cpu_total_lbl.setStyleSheet("color: #4F8CFF; font-weight: 700; font-size: 14px;")
        cpu_header.addWidget(cpu_title)
        cpu_header.addStretch()
        cpu_header.addWidget(self.cpu_total_lbl)
        cpu_layout.addLayout(cpu_header)

        # Large CPU Live Chart
        self.cpu_live_chart = RealtimeSparkline(max_points=60, color_hex="#4F8CFF")
        self.cpu_live_chart.setFixedHeight(75)
        cpu_layout.addWidget(self.cpu_live_chart)

        # Per-core breakdown container
        core_lbl = QLabel("Logical CPU Core Allocation:")
        core_lbl.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px;")
        cpu_layout.addWidget(core_lbl)

        self.cores_grid = QGridLayout()
        self.cores_grid.setSpacing(8)
        self.core_bars: List[QProgressBar] = []
        self.core_labels: List[QLabel] = []
        cpu_layout.addLayout(self.cores_grid)

        self.content_layout.addWidget(cpu_panel)

        # ---------------- Section 2: RAM Memory In-Depth ----------------
        ram_panel = QFrame()
        ram_panel.setProperty("class", "card-panel")
        ram_layout = QVBoxLayout(ram_panel)
        ram_layout.setSpacing(12)

        ram_header = QHBoxLayout()
        ram_title = QLabel("RAM System Memory Breakdown")
        ram_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F8FAFC;")
        self.ram_detail_lbl = QLabel("Used: 0.0 GB / 0.0 GB")
        self.ram_detail_lbl.setStyleSheet("color: #38BDF8; font-weight: 700; font-size: 14px;")
        ram_header.addWidget(ram_title)
        ram_header.addStretch()
        ram_header.addWidget(self.ram_detail_lbl)
        ram_layout.addLayout(ram_header)

        self.ram_live_chart = RealtimeSparkline(max_points=60, color_hex="#38BDF8")
        self.ram_live_chart.setFixedHeight(75)
        ram_layout.addWidget(self.ram_live_chart)

        self.ram_desc = QLabel(
            "Physical memory allocation directly affects virtual memory paging. "
            "When RAM usage approaches 85%, Windows or Linux actively swaps inactive pages to disk."
        )
        self.ram_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ram_layout.addWidget(self.ram_desc)
        self.content_layout.addWidget(ram_panel)

        # ---------------- Section 3: Disk Capacity vs Disk I/O Activity ----------------
        disk_panel = QFrame()
        disk_panel.setProperty("class", "card-panel")
        disk_layout = QVBoxLayout(disk_panel)
        disk_layout.setSpacing(12)

        disk_header = QHBoxLayout()
        disk_title = QLabel("Storage: Capacity Utilization vs. Real-Time I/O Activity")
        disk_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F8FAFC;")
        disk_header.addWidget(disk_title)
        disk_header.addStretch()
        disk_layout.addLayout(disk_header)

        distinction_note = QLabel(
            "<b>Architectural Distinction:</b> Disk <i>Capacity</i> reflects persistent space occupied on the partition, "
            "whereas Disk <i>I/O</i> measures active read/write data transfer throughput. They are distinct metrics."
        )
        distinction_note.setStyleSheet("background-color: #111A29; color: #E2E8F0; padding: 8px 12px; border-radius: 6px; font-size: 12px;")
        distinction_note.setWordWrap(True)
        disk_layout.addWidget(distinction_note)

        io_row = QHBoxLayout()
        self.disk_read_card = StatCard(title="Disk Read Throughput", unit=" MB/s", chart_color="#22C55E")
        self.disk_write_card = StatCard(title="Disk Write Throughput", unit=" MB/s", chart_color="#F59E0B")
        io_row.addWidget(self.disk_read_card)
        io_row.addWidget(self.disk_write_card)
        disk_layout.addLayout(io_row)

        self.content_layout.addWidget(disk_panel)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _on_interval_selected(self, index: int):
        intervals = [1.0, 2.0, 5.0, 10.0]
        if index < len(intervals):
            self.interval_changed.emit(intervals[index])

    def update_telemetry(self, reading: SystemReading):
        """Update live charts and core bars with reading."""
        self.cpu_total_lbl.setText(f"Total: {reading.cpu_percent:.1f}%")
        self.cpu_live_chart.add_point(reading.cpu_percent)

        # Update per-core layout dynamically if not yet created
        cores = reading.cpu_cores_percent
        if len(self.core_bars) != len(cores):
            # Clean and recreate
            for b in self.core_bars:
                b.deleteLater()
            for l in self.core_labels:
                l.deleteLater()
            self.core_bars.clear()
            self.core_labels.clear()

            cols = 4
            for i, c_pct in enumerate(cores):
                r = i // cols
                c = (i % cols) * 2
                lbl = QLabel(f"Core {i}:")
                lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setFixedHeight(8)
                bar.setTextVisible(False)
                bar.setValue(int(c_pct))
                self.cores_grid.addWidget(lbl, r, c)
                self.cores_grid.addWidget(bar, r, c + 1)
                self.core_labels.append(lbl)
                self.core_bars.append(bar)
        else:
            for i, c_pct in enumerate(cores):
                self.core_bars[i].setValue(int(c_pct))
                self.core_labels[i].setText(f"Core {i} ({c_pct:.0f}%):")

        # RAM updates
        used_gb = reading.ram_used_bytes / (1024 ** 3)
        total_gb = reading.ram_total_bytes / (1024 ** 3)
        self.ram_detail_lbl.setText(f"Used: {used_gb:.1f} / {total_gb:.1f} GB ({reading.ram_percent:.1f}%)")
        self.ram_live_chart.add_point(reading.ram_percent)

        # Disk I/O updates
        read_mb = reading.disk_read_bytes_sec / (1024 * 1024)
        write_mb = reading.disk_write_bytes_sec / (1024 * 1024)
        self.disk_read_card.update_metric(
            value=min(100.0, read_mb),
            value_text=f"{read_mb:.2f} MB/s",
            severity="healthy" if read_mb < 50 else ("warning" if read_mb < 150 else "critical"),
            interpretation=f"Current read transfer rate: {read_mb:.2f} MB/s"
        )
        self.disk_write_card.update_metric(
            value=min(100.0, write_mb),
            value_text=f"{write_mb:.2f} MB/s",
            severity="healthy" if write_mb < 50 else ("warning" if write_mb < 150 else "critical"),
            interpretation=f"Current write transfer rate: {write_mb:.2f} MB/s"
        )
