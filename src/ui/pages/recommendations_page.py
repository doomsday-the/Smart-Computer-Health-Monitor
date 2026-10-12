"""
Recommendations Page.
Displays targeted, actionable, safe advisory recommendations with priority sorting
and safe step-by-step guidance.
"""

from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea,
    QFrame
)
from src.ui.components.recommendation_card import RecommendationCard
from src.analysis.recommendation_engine import Recommendation


class RecommendationsPage(QWidget):
    """Smart advisory guidance interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_recs: List[Recommendation] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Actionable Recommendations")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #F8FAFC;")
        sub_lbl = QLabel("Targeted, non-destructive guidance mapped directly to active operating-system insights")
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Priority Filter
        lbl_prio = QLabel("Priority:")
        lbl_prio.setStyleSheet("color: #94A3B8; font-weight: 600;")
        self.combo_prio = QComboBox()
        self.combo_prio.addItems(["All Priorities", "High Priority", "Medium Priority", "Low Priority"])
        self.combo_prio.currentIndexChanged.connect(self._render_recommendations)
        header_row.addWidget(lbl_prio)
        header_row.addWidget(self.combo_prio)

        main_layout.addLayout(header_row)

        # Advisory Safety Banner
        banner = QFrame()
        banner.setStyleSheet("background-color: #111A29; border-left: 3px solid #22C55E; border-radius: 4px; padding: 10px 14px;")
        b_lay = QVBoxLayout(banner)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lbl = QLabel(
            "<b>Strict Advisory Guarantee:</b> This application will never automatically delete personal files, "
            "forcefully kill system services, or tamper with system registry settings. Recommendations represent safe "
            "advisory guidance for the user."
        )
        b_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        b_lbl.setWordWrap(True)
        b_lay.addWidget(b_lbl)
        main_layout.addWidget(banner)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.recs_layout = QVBoxLayout(content_widget)
        self.recs_layout.setContentsMargins(0, 0, 0, 0)
        self.recs_layout.setSpacing(14)

        self.empty_lbl = QLabel("No active recommendations required. Computer resources are balanced and healthy.")
        self.empty_lbl.setStyleSheet("color: #64748B; font-size: 14px; padding: 40px 0;")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.recs_layout.addWidget(self.empty_lbl)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def update_recommendations(self, recs: List[Recommendation]):
        """Receive updated recommendations from controller."""
        self._current_recs = recs
        self._render_recommendations()

    def _render_recommendations(self):
        while self.recs_layout.count():
            item = self.recs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filter_idx = self.combo_prio.currentIndex()
        filtered: List[Recommendation] = []
        for r in self._current_recs:
            if filter_idx == 1 and r.priority != "High":
                continue
            if filter_idx == 2 and r.priority != "Medium":
                continue
            if filter_idx == 3 and r.priority != "Low":
                continue
            filtered.append(r)

        if not filtered:
            lbl = QLabel("No active recommendations match the selected filter. System is healthy.")
            lbl.setStyleSheet("color: #64748B; font-size: 14px; padding: 40px 0;")
            lbl.setAlignment(Qt.AlignCenter)
            self.recs_layout.addWidget(lbl)
            return

        for r in filtered:
            card = RecommendationCard(r.to_dict())
            self.recs_layout.addWidget(card)

        self.recs_layout.addStretch()
