"""
Alerts Management Page.
Displays real-time and historical alerts with severity filtering,
acknowledgement actions, resolution status, and duplicate suppression tracking.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from src.alerts.alert_manager import AlertManager, AlertItem
from src.database.db_manager import DatabaseManager


class AlertsPage(QWidget):
    """Alert review and lifecycle management interface."""

    def __init__(self, alert_manager: AlertManager, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.alert_mgr = alert_manager
        self.db = db_manager
        self._alerts_cache: List[Dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Alert Management")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #F8FAFC;")
        sub_lbl = QLabel("Track, acknowledge, and resolve resource warnings with automated duplicate suppression")
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_refresh = QPushButton("Refresh Alerts")
        self.btn_refresh.setProperty("class", "btn-secondary")
        self.btn_refresh.clicked.connect(self.refresh_alerts)
        header_row.addWidget(self.btn_refresh)
        layout.addLayout(header_row)

        # Filters toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search alerts by keyword or resource...")
        self.search_input.textChanged.connect(self._filter_and_populate)
        toolbar.addWidget(self.search_input, stretch=2)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet("color: #94A3B8; font-weight: 600;")
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Unresolved Only", "All Alerts"])
        self.combo_status.currentIndexChanged.connect(self.refresh_alerts)
        toolbar.addWidget(lbl_status)
        toolbar.addWidget(self.combo_status)

        lbl_sev = QLabel("Severity:")
        lbl_sev.setStyleSheet("color: #94A3B8; font-weight: 600;")
        self.combo_sev = QComboBox()
        self.combo_sev.addItems(["All Severities", "Critical", "Warning", "Info"])
        self.combo_sev.currentIndexChanged.connect(self._filter_and_populate)
        toolbar.addWidget(lbl_sev)
        toolbar.addWidget(self.combo_sev)

        layout.addLayout(toolbar)

        # Alerts Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp (UTC)", "Severity", "Resource", "Alert Message & Guidance", "Ack", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, stretch=1)

        # Initial load
        self.refresh_alerts()

    def refresh_alerts(self):
        """Fetch alerts from database according to status filter."""
        only_active = (self.combo_status.currentIndex() == 0)
        self._alerts_cache = self.db.get_alerts(only_active=only_active, limit=100)
        self._filter_and_populate()

    def _filter_and_populate(self):
        query = self.search_input.text().strip().lower()
        sev_filter = self.combo_sev.currentText().lower()

        filtered = []
        for a in self._alerts_cache:
            if sev_filter != "all severities" and a.get("severity", "").lower() != sev_filter:
                continue
            if query:
                combined = f"{a.get('message', '')} {a.get('resource', '')}".lower()
                if query not in combined:
                    continue
            filtered.append(a)

        self.table.setRowCount(len(filtered))
        for row, a in enumerate(filtered):
            # ID
            item_id = QTableWidgetItem(str(a.get("id", "")))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)

            # Timestamp
            ts_str = str(a.get("timestamp", ""))[:19].replace("T", " ")
            item_ts = QTableWidgetItem(ts_str)
            item_ts.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_ts)

            # Severity
            sev = a.get("severity", "info").upper()
            item_sev = QTableWidgetItem(sev)
            item_sev.setTextAlignment(Qt.AlignCenter)
            if sev == "CRITICAL":
                item_sev.setForeground(Qt.red)
            elif sev == "WARNING":
                item_sev.setForeground(Qt.yellow)
            else:
                item_sev.setForeground(Qt.cyan)
            self.table.setItem(row, 2, item_sev)

            # Resource
            item_res = QTableWidgetItem(a.get("resource", "System"))
            item_res.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_res)

            # Message
            item_msg = QTableWidgetItem(a.get("message", ""))
            self.table.setItem(row, 4, item_msg)

            # Ack
            is_ack = bool(a.get("acknowledged", 0))
            item_ack = QTableWidgetItem("Yes" if is_ack else "No")
            item_ack.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, item_ack)

            # Action Button
            alert_id = a.get("id")
            is_resolved = bool(a.get("resolved", 0))
            if not is_resolved:
                btn_resolve = QPushButton("Resolve")
                btn_resolve.setProperty("class", "btn-secondary")
                btn_resolve.clicked.connect(lambda _, aid=alert_id: self._resolve_alert_action(aid))
                self.table.setCellWidget(row, 6, btn_resolve)
            else:
                lbl_res = QLabel("Resolved")
                lbl_res.setStyleSheet("color: #22C55E; font-weight: 600;")
                lbl_res.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row, 6, lbl_res)

    def _resolve_alert_action(self, alert_id: int):
        self.alert_mgr.resolve_alert(alert_id)
        self.refresh_alerts()
