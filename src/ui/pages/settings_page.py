"""
Settings Page.
Configures monitoring thresholds, sustained sample windows, alert cooldowns,
retention policies, and provides safe database maintenance actions.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox,
    QSpinBox, QFrame, QScrollArea, QMessageBox
)
from src.config import MonitorSettings
from src.database.db_manager import DatabaseManager


class SettingsPage(QWidget):
    """Configuration management view."""

    settings_updated = Signal(object)  # MonitorSettings

    def __init__(self, current_settings: MonitorSettings, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.settings = current_settings
        self.db = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Configuration & Threshold Settings")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #172033;")
        sub_lbl = QLabel("Calibrate diagnostic thresholds, sampling intervals, and database retention rules")
        sub_lbl.setStyleSheet("color: #667085; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.setProperty("class", "btn-secondary")
        self.btn_reset.clicked.connect(self._reset_defaults)
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.clicked.connect(self._save_settings)

        header_row.addWidget(self.btn_reset)
        header_row.addWidget(self.btn_save)
        main_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # ---------------- Section 1: Resource Thresholds ----------------
        thresh_card = QFrame()
        thresh_card.setProperty("class", "card-panel")
        thresh_layout = QVBoxLayout(thresh_card)
        thresh_layout.setSpacing(12)

        t_title = QLabel("1. Diagnostic Resource Thresholds (%)")
        t_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #172033;")
        thresh_layout.addWidget(t_title)

        # CPU Thresholds
        self.cpu_warn_spin = self._add_double_row(thresh_layout, "CPU Warning Threshold (%):", 10.0, 95.0, self.settings.cpu_warning_pct)
        self.cpu_crit_spin = self._add_double_row(thresh_layout, "CPU Critical Threshold (%):", 20.0, 99.0, self.settings.cpu_critical_pct)

        # RAM Thresholds
        self.ram_warn_spin = self._add_double_row(thresh_layout, "RAM Warning Threshold (%):", 10.0, 95.0, self.settings.ram_warning_pct)
        self.ram_crit_spin = self._add_double_row(thresh_layout, "RAM Critical Threshold (%):", 20.0, 99.0, self.settings.ram_critical_pct)

        # Disk Thresholds
        self.disk_warn_spin = self._add_double_row(thresh_layout, "Disk Used Warning Threshold (%):", 10.0, 95.0, self.settings.disk_warning_pct)
        self.disk_crit_spin = self._add_double_row(thresh_layout, "Disk Used Critical Threshold (%):", 20.0, 99.0, self.settings.disk_critical_pct)

        # Battery Thresholds
        self.batt_warn_spin = self._add_double_row(thresh_layout, "Battery Warning Threshold (%):", 5.0, 60.0, self.settings.battery_warning_pct)
        self.batt_crit_spin = self._add_double_row(thresh_layout, "Battery Critical Threshold (%):", 1.0, 30.0, self.settings.battery_critical_pct)

        self.content_layout.addWidget(thresh_card)

        # ---------------- Section 2: Timing, Cooldown & Persistence ----------------
        timing_card = QFrame()
        timing_card.setProperty("class", "card-panel")
        timing_layout = QVBoxLayout(timing_card)
        timing_layout.setSpacing(12)

        time_title = QLabel("2. Monitoring Cadence & Duplicate Suppression")
        time_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #172033;")
        timing_layout.addWidget(time_title)

        self.interval_spin = self._add_double_row(timing_layout, "Telemetry Sampling Interval (seconds):", 0.5, 60.0, self.settings.monitoring_interval_sec)
        self.sustained_spin = self._add_int_row(timing_layout, "Sustained Samples (consecutive counts before alert):", 1, 30, self.settings.sustained_samples)
        self.cooldown_spin = self._add_double_row(timing_layout, "Alert Cooldown Window (seconds):", 5.0, 600.0, self.settings.alert_cooldown_sec)
        self.retention_spin = self._add_int_row(timing_layout, "Database History Retention (days):", 1, 90, self.settings.history_retention_days)

        self.content_layout.addWidget(timing_card)

        # ---------------- Section 3: Maintenance Actions ----------------
        maint_card = QFrame()
        maint_card.setProperty("class", "card-panel")
        maint_layout = QVBoxLayout(maint_card)
        maint_layout.setSpacing(12)

        m_title = QLabel("3. Database Maintenance")
        m_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #172033;")
        maint_layout.addWidget(m_title)

        m_desc = QLabel("Safely clear local historical metric records and alerts stored in SQLite.")
        m_desc.setStyleSheet("color: #667085; font-size: 12px;")
        maint_layout.addWidget(m_desc)

        btn_clear = QPushButton("Clear Historical Telemetry Data")
        btn_clear.setProperty("class", "btn-danger")
        btn_clear.clicked.connect(self._clear_history_data)
        maint_layout.addWidget(btn_clear)

        self.content_layout.addWidget(maint_card)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _add_double_row(self, layout: QVBoxLayout, label_text: str, min_val: float, max_val: float, cur_val: float) -> QDoubleSpinBox:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #344054; font-size: 13px;")
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(cur_val)
        spin.setSingleStep(1.0)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(spin)
        layout.addLayout(row)
        return spin

    def _add_int_row(self, layout: QVBoxLayout, label_text: str, min_val: int, max_val: int, cur_val: int) -> QSpinBox:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #344054; font-size: 13px;")
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(cur_val)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(spin)
        layout.addLayout(row)
        return spin

    def _save_settings(self):
        new_settings = MonitorSettings(
            cpu_warning_pct=self.cpu_warn_spin.value(),
            cpu_critical_pct=self.cpu_crit_spin.value(),
            ram_warning_pct=self.ram_warn_spin.value(),
            ram_critical_pct=self.ram_crit_spin.value(),
            disk_warning_pct=self.disk_warn_spin.value(),
            disk_critical_pct=self.disk_crit_spin.value(),
            battery_warning_pct=self.batt_warn_spin.value(),
            battery_critical_pct=self.batt_crit_spin.value(),
            monitoring_interval_sec=self.interval_spin.value(),
            sustained_samples=self.sustained_spin.value(),
            alert_cooldown_sec=self.cooldown_spin.value(),
            history_retention_days=self.retention_spin.value()
        )

        valid, msg = new_settings.validate()
        if not valid:
            QMessageBox.critical(self, "Validation Error", f"Cannot apply settings:\n{msg}")
            return

        self.settings = new_settings
        self.settings_updated.emit(self.settings)
        QMessageBox.information(self, "Settings Saved", "Configuration updated successfully and applied in real-time.")

    def _reset_defaults(self):
        defaults = MonitorSettings()
        self.cpu_warn_spin.setValue(defaults.cpu_warning_pct)
        self.cpu_crit_spin.setValue(defaults.cpu_critical_pct)
        self.ram_warn_spin.setValue(defaults.ram_warning_pct)
        self.ram_crit_spin.setValue(defaults.ram_critical_pct)
        self.disk_warn_spin.setValue(defaults.disk_warning_pct)
        self.disk_crit_spin.setValue(defaults.disk_critical_pct)
        self.batt_warn_spin.setValue(defaults.battery_warning_pct)
        self.batt_crit_spin.setValue(defaults.battery_critical_pct)
        self.interval_spin.setValue(defaults.monitoring_interval_sec)
        self.sustained_spin.setValue(defaults.sustained_samples)
        self.cooldown_spin.setValue(defaults.alert_cooldown_sec)
        self.retention_spin.setValue(defaults.history_retention_days)

    def _clear_history_data(self):
        reply = QMessageBox.question(
            self,
            "Confirm Data Purge",
            "Are you sure you want to permanently clear all historical metrics and alert logs?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.clear_all_history()
            QMessageBox.information(self, "History Cleared", "All historical records have been purged from SQLite.")
