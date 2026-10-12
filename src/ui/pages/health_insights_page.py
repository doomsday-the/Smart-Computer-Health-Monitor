"""
Health Insights Page - The Interpretation Layer UI.
Presents detailed explainable diagnoses of detected system performance conditions
using structured evidence, OS principles, and advisory guidance.
"""

from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea,
    QFrame
)
from src.ui.components.insight_card import InsightCard
from src.analysis.interpretation_engine import Insight


class HealthInsightsPage(QWidget):
    """Explainable diagnostics and interpretation view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_insights: List[Insight] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Explainable Health Insights")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #F8FAFC;")
        sub_lbl = QLabel("The Interpretation Layer: Converting raw OS telemetry into evidence-based diagnoses")
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Severity Filter
        lbl_filter = QLabel("Filter:")
        lbl_filter.setStyleSheet("color: #94A3B8; font-weight: 600;")
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["All Severities", "Critical Only", "Warning Only", "Normal / Info"])
        self.combo_filter.currentIndexChanged.connect(self._render_insights)
        header_row.addWidget(lbl_filter)
        header_row.addWidget(self.combo_filter)

        main_layout.addLayout(header_row)

        # Explanation Banner
        banner = QFrame()
        banner.setStyleSheet("background-color: #111A29; border-left: 3px solid #4F8CFF; border-radius: 4px; padding: 10px 14px;")
        b_lay = QVBoxLayout(banner)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lbl = QLabel(
            "<b>The Core Research Contribution:</b> Rather than reporting isolated numbers (e.g. 92% CPU), "
            "each card below answers: <i>What happened? What evidence supports it? Why does it matter? "
            "What might have caused it? What safe steps should you take next?</i>"
        )
        b_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        b_lbl.setWordWrap(True)
        b_lay.addWidget(b_lbl)
        main_layout.addWidget(banner)

        # Scroll Area for Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.cards_layout = QVBoxLayout(content_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(14)

        self.empty_lbl = QLabel("No abnormal health conditions detected. All monitored resources are operating within healthy parameters.")
        self.empty_lbl.setStyleSheet("color: #64748B; font-size: 14px; padding: 40px 0;")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.cards_layout.addWidget(self.empty_lbl)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def update_insights(self, insights: List[Insight]):
        """Receive updated insights list from monitor worker."""
        self._current_insights = insights
        self._render_insights()

    def _render_insights(self):
        # Clear existing card widgets
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filter_idx = self.combo_filter.currentIndex()
        # 0: All, 1: Critical, 2: Warning, 3: Info
        filtered: List[Insight] = []
        for ins in self._current_insights:
            if filter_idx == 1 and ins.severity != "critical":
                continue
            if filter_idx == 2 and ins.severity != "warning":
                continue
            if filter_idx == 3 and ins.severity not in ("info", "normal"):
                continue
            filtered.append(ins)

        if not filtered:
            lbl = QLabel("No active insights match the selected filter. System health is normal.")
            lbl.setStyleSheet("color: #64748B; font-size: 14px; padding: 40px 0;")
            lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(lbl)
            return

        for ins in filtered:
            card = InsightCard(ins.to_dict())
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
