"""
Reusable Stat Card widget.
Displays resource values, sparklines, progress bars, and status badges.
"""

from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from src.ui.components.status_badge import StatusBadge
from src.ui.components.mini_chart import RealtimeSparkline


class StatCard(QFrame):
    """Interactive card for system resources with sparklines and status badges."""

    def __init__(
        self,
        title: str,
        unit: str = "%",
        chart_color: str = "#4F8CFF",
        has_chart: bool = True,
        parent=None
    ):
        super().__init__(parent)
        self.setProperty("class", "card-panel")
        self.unit = unit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top row: Title and Badge
        top_row = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 13px;")
        self.badge = StatusBadge("Healthy", "healthy")
        top_row.addWidget(self.title_lbl)
        top_row.addStretch()
        top_row.addWidget(self.badge)
        layout.addLayout(top_row)

        # Middle row: Large Value & Subtitle
        mid_row = QHBoxLayout()
        self.val_lbl = QLabel("--")
        self.val_lbl.setStyleSheet("color: #F8FAFC; font-size: 26px; font-weight: 700;")
        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        mid_row.addWidget(self.val_lbl)
        mid_row.addStretch()
        mid_row.addWidget(self.sub_lbl)
        layout.addLayout(mid_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        # Sparkline chart
        self.has_chart = has_chart
        if has_chart:
            self.chart = RealtimeSparkline(color_hex=chart_color)
            layout.addWidget(self.chart)
        else:
            self.chart = None

        # Interpretation footer
        self.interp_lbl = QLabel("Monitoring baseline activity...")
        self.interp_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; margin-top: 4px;")
        self.interp_lbl.setWordWrap(True)
        layout.addWidget(self.interp_lbl)

    def update_metric(
        self,
        value: float,
        value_text: Optional[str] = None,
        subtitle: Optional[str] = None,
        severity: str = "healthy",
        interpretation: Optional[str] = None
    ):
        display_str = value_text if value_text else f"{value:.1f}{self.unit}"
        self.val_lbl.setText(display_str)
        self.progress_bar.setValue(int(max(0, min(100, value))))

        if subtitle is not None:
            self.sub_lbl.setText(subtitle)

        self.badge.set_severity(severity, severity.capitalize())

        if interpretation:
            self.interp_lbl.setText(interpretation)

        if self.chart:
            self.chart.add_point(value)
