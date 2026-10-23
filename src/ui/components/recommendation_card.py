"""
Recommendation Card component.
Displays specific, actionable, safe advisory guidance.
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel
)
from src.ui.components.status_badge import StatusBadge


class RecommendationCard(QFrame):
    """Card presenting structured advisory guidance and safe actionable steps."""

    def __init__(self, rec_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setProperty("class", "card-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # 1. Header: Title, Priority, Resource
        header = QHBoxLayout()
        title_lbl = QLabel(rec_data.get("title", "Advisory Recommendation"))
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #172033;")
        header.addWidget(title_lbl)
        header.addStretch()

        resource = rec_data.get("related_resource", "System")
        res_lbl = QLabel(f"[{resource}]")
        res_lbl.setStyleSheet("color: #0891B2; font-weight: 600; font-size: 12px;")
        header.addWidget(res_lbl)

        prio = rec_data.get("priority", "Medium")
        prio_badge = StatusBadge(
            f"{prio} Priority",
            "critical" if prio == "High" else ("warning" if prio == "Medium" else "good")
        )
        header.addWidget(prio_badge)
        layout.addLayout(header)

        # 2. Reason & Measurement
        reason_text = rec_data.get("reason", "")
        measurement = rec_data.get("related_measurement", "")
        reason_lbl = QLabel(f"<b>Diagnosis:</b> {reason_text} (Observed: {measurement})")
        reason_lbl.setStyleSheet("color: #667085; font-size: 12px;")
        reason_lbl.setWordWrap(True)
        layout.addWidget(reason_lbl)

        # 3. Action Checklist Steps
        steps_box = QFrame()
        steps_box.setStyleSheet("background-color: #F8FAFC; border-radius: 6px; padding: 10px;")
        steps_layout = QVBoxLayout(steps_box)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(6)

        steps_title = QLabel("Suggested Action Steps:")
        steps_title.setStyleSheet("color: #2563EB; font-weight: 600; font-size: 12px;")
        steps_layout.addWidget(steps_title)

        steps_list: List[str] = rec_data.get("suggested_steps", [])
        for i, step in enumerate(steps_list, 1):
            s_lbl = QLabel(f"<b>{i}.</b> {step}")
            s_lbl.setStyleSheet("color: #344054; font-size: 12px;")
            s_lbl.setWordWrap(True)
            steps_layout.addWidget(s_lbl)

        layout.addWidget(steps_box)

        # 4. Expected Benefit
        benefit = rec_data.get("expected_benefit", "")
        ben_lbl = QLabel(f"<b>Expected Benefit:</b> {benefit}")
        ben_lbl.setStyleSheet("color: #16A34A; font-size: 12px;")
        ben_lbl.setWordWrap(True)
        layout.addWidget(ben_lbl)

        # 5. Safety Advisory Note
        safety = rec_data.get("safety_note", "")
        if safety:
            safety_box = QFrame()
            safety_box.setStyleSheet("background-color: rgba(245, 158, 11, 0.1); border-left: 3px solid #D97706; border-radius: 4px; padding: 6px 10px;")
            s_layout = QVBoxLayout(safety_box)
            s_layout.setContentsMargins(0, 0, 0, 0)
            safety_lbl = QLabel(f"<b>Safety Notice:</b> {safety}")
            safety_lbl.setStyleSheet("color: #D97706; font-size: 11px;")
            safety_lbl.setWordWrap(True)
            s_layout.addWidget(safety_lbl)
            layout.addWidget(safety_box)
