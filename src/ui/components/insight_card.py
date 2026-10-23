"""
Insight Card component.
Presents structured explainable diagnoses with the 9-point explainability framework:
1. Detection, 2. Observed facts, 3. Significance, 4. Evidence,
5. Contributing factors, 6. Confidence, 7. User Action, 8. Verification, 9. Technical Details.
"""

import json
from typing import Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from src.ui.components.status_badge import StatusBadge


class InsightCard(QFrame):
    """Rich card rendering an explainable insight."""

    def __init__(self, insight_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setProperty("class", "card-panel")
        self.data = insight_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # 1. Header: Title, Resource, Severity, Status
        header_layout = QHBoxLayout()
        title_text = insight_data.get("title", "Resource Notice")
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #172033;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()

        resource = insight_data.get("resource", "System")
        self.res_badge = QLabel(f"[{resource}]")
        self.res_badge.setStyleSheet("color: #0891B2; font-weight: 600; font-size: 12px;")
        header_layout.addWidget(self.res_badge)

        severity = insight_data.get("severity", "info")
        self.sev_badge = StatusBadge(severity.capitalize(), severity)
        header_layout.addWidget(self.sev_badge)

        status = insight_data.get("status", "new").upper()
        self.status_lbl = QLabel(f"• {status}")
        self.status_lbl.setStyleSheet("color: #667085; font-size: 11px; font-weight: 600;")
        header_layout.addWidget(self.status_lbl)

        layout.addLayout(header_layout)

        # 2. Observed Fact & Rule
        obs_val = insight_data.get("observed_value", "N/A")
        rule = insight_data.get("rule_triggered", "")
        fact_box = QFrame()
        fact_box.setStyleSheet("background-color: #F8FAFC; border-radius: 6px; padding: 8px 12px;")
        fact_layout = QVBoxLayout(fact_box)
        fact_layout.setContentsMargins(0, 0, 0, 0)
        fact_layout.setSpacing(3)

        lbl_fact_title = QLabel("1. Observed Measurement & Threshold:")
        lbl_fact_title.setStyleSheet("color: #0891B2; font-weight: 600; font-size: 11px;")
        lbl_fact_val = QLabel(f"<b>Observed:</b> {obs_val}  |  <b>Rule:</b> {rule}")
        lbl_fact_val.setStyleSheet("color: #344054; font-size: 12px;")
        lbl_fact_val.setWordWrap(True)
        fact_layout.addWidget(lbl_fact_title)
        fact_layout.addWidget(lbl_fact_val)
        layout.addWidget(fact_box)

        # 3. Why It Matters (Operating System Context)
        why_title = QLabel("2. Operating System Impact:")
        why_title.setStyleSheet("color: #667085; font-weight: 600; font-size: 11px; margin-top: 4px;")
        layout.addWidget(why_title)

        why_desc = QLabel(insight_data.get("explanation", ""))
        why_desc.setStyleSheet("color: #172033; font-size: 13px; line-height: 1.4;")
        why_desc.setWordWrap(True)
        layout.addWidget(why_desc)

        # 4. Contributing Factors (Distinguished from guaranteed proof)
        cause_title = QLabel("3. Plausible Contributing Factors (Advisory):")
        cause_title.setStyleSheet("color: #667085; font-weight: 600; font-size: 11px;")
        layout.addWidget(cause_title)

        cause_desc = QLabel(insight_data.get("possible_cause", "No specific rogue processes identified."))
        cause_desc.setStyleSheet("color: #667085; font-size: 12px; font-style: italic;")
        cause_desc.setWordWrap(True)
        layout.addWidget(cause_desc)

        # 5. Recommendation & Verification
        action_box = QFrame()
        action_box.setStyleSheet("background-color: #172740; border-left: 3px solid #2563EB; border-radius: 4px; padding: 10px;")
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(6, 4, 6, 4)
        action_layout.setSpacing(4)

        rec_title = QLabel("4. Actionable Next Step & Verification:")
        rec_title.setStyleSheet("color: #2563EB; font-weight: 600; font-size: 11px;")
        rec_desc = QLabel(insight_data.get("recommendation", "Continue normal usage."))
        rec_desc.setStyleSheet("color: #344054; font-size: 13px; font-weight: 500;")
        rec_desc.setWordWrap(True)

        verify_desc = QLabel("<b>Verification:</b> Observe resource history after action to verify whether usage normalizes.")
        verify_desc.setStyleSheet("color: #667085; font-size: 11px;")

        action_layout.addWidget(rec_title)
        action_layout.addWidget(rec_desc)
        action_layout.addWidget(verify_desc)
        layout.addWidget(action_box)

        # 6. Confidence & Expandable Technical Details
        footer_layout = QHBoxLayout()
        conf_lbl = QLabel(f"Confidence: {insight_data.get('confidence_label', 'High')}")
        conf_lbl.setStyleSheet("color: #0891B2; font-size: 11px; font-weight: 600;")
        footer_layout.addWidget(conf_lbl)
        footer_layout.addStretch()

        self.toggle_btn = QPushButton("Show Technical Evidence ▼")
        self.toggle_btn.setStyleSheet("background: transparent; color: #667085; border: none; font-size: 11px;")
        self.toggle_btn.clicked.connect(self._toggle_evidence)
        footer_layout.addWidget(self.toggle_btn)
        layout.addLayout(footer_layout)

        # Collapsible Evidence Box
        self.evidence_box = QFrame()
        self.evidence_box.setStyleSheet("background-color: #0F172A; border: 1px solid #172033; border-radius: 6px; padding: 10px;")
        self.evidence_box.setVisible(False)
        ev_layout = QVBoxLayout(self.evidence_box)
        
        evidence_dict = insight_data.get("evidence") or {}
        if not evidence_dict and insight_data.get("evidence_json"):
            try:
                evidence_dict = json.loads(insight_data["evidence_json"])
            except Exception:
                evidence_dict = {}

        evidence_str = json.dumps(evidence_dict, indent=2)
        ev_lbl = QLabel(f"<pre style='color: #0891B2; font-family: monospace; font-size: 11px;'>{evidence_str}</pre>")
        ev_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ev_layout.addWidget(ev_lbl)
        layout.addWidget(self.evidence_box)

    def _toggle_evidence(self):
        is_visible = self.evidence_box.isVisible()
        self.evidence_box.setVisible(not is_visible)
        self.toggle_btn.setText("Hide Technical Evidence ▲" if not is_visible else "Show Technical Evidence ▼")
