"""
Process Explorer Page.
Displays interactive operating system process table with real-time sorting,
filtering, searching, memory inspection, and educational notes on resource utilization.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSplitter
)
from src.monitoring.process_monitor import ProcessInfo


class ProcessExplorerPage(QWidget):
    """Real-time Operating System Process Explorer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_processes: List[ProcessInfo] = []
        self._filtered_processes: List[ProcessInfo] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Process Explorer")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #172033;")
        sub_lbl = QLabel("Inspect active operating system tasks, thread owners, CPU usage, and memory working sets")
        sub_lbl.setStyleSheet("color: #667085; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.proc_count_lbl = QLabel("Processes: 0")
        self.proc_count_lbl.setStyleSheet("color: #0891B2; font-weight: 600; font-size: 13px;")
        header_row.addWidget(self.proc_count_lbl)
        layout.addLayout(header_row)

        # Scientific Note Banner
        note_box = QFrame()
        note_box.setStyleSheet("background-color: #F8FAFC; border-left: 3px solid #0891B2; border-radius: 4px; padding: 8px 12px;")
        nb_layout = QVBoxLayout(note_box)
        nb_layout.setContentsMargins(0, 0, 0, 0)
        note_lbl = QLabel(
            "<b>Operating System Note:</b> High CPU or memory consumption is a measure of workload demand, "
            "not evidence of malware or software corruption. Heavy compilation, indexing, or multimedia rendering "
            "legitimately utilizes full core capacity."
        )
        note_lbl.setStyleSheet("color: #667085; font-size: 12px;")
        note_lbl.setWordWrap(True)
        nb_layout.addWidget(note_lbl)
        layout.addWidget(note_box)

        # Search and Filter Toolbar
        toolbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search processes by name or PID...")
        self.search_box.textChanged.connect(self._filter_table)
        toolbar.addWidget(self.search_box, stretch=2)

        self.btn_sort_cpu = QPushButton("Sort by CPU ▼")
        self.btn_sort_cpu.setProperty("class", "btn-secondary")
        self.btn_sort_cpu.clicked.connect(self._sort_by_cpu)
        toolbar.addWidget(self.btn_sort_cpu)

        self.btn_sort_mem = QPushButton("Sort by Memory ▼")
        self.btn_sort_mem.setProperty("class", "btn-secondary")
        self.btn_sort_mem.clicked.connect(self._sort_by_mem)
        toolbar.addWidget(self.btn_sort_mem)

        layout.addLayout(toolbar)

        # Main Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "PID", "Process Name", "CPU %", "RAM %", "Memory (RSS)", "Status", "User / Owner"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self.table, stretch=1)

        # Process Detail Inspector Box
        self.detail_frame = QFrame()
        self.detail_frame.setProperty("class", "card-panel")
        self.detail_layout = QHBoxLayout(self.detail_frame)
        self.detail_layout.setContentsMargins(14, 10, 14, 10)
        self.detail_lbl = QLabel("Select a process in the table above to view detailed execution metrics.")
        self.detail_lbl.setStyleSheet("color: #667085; font-size: 12px;")
        self.detail_layout.addWidget(self.detail_lbl)
        layout.addWidget(self.detail_frame)

    def update_processes(self, processes: List[ProcessInfo]):
        """Receive updated processes list from monitor worker."""
        self._all_processes = processes
        self.proc_count_lbl.setText(f"Active Processes: {len(processes)}")
        self._filter_table()

    def _filter_table(self):
        query = self.search_box.text().strip().lower()
        if not query:
            self._filtered_processes = list(self._all_processes)
        else:
            self._filtered_processes = [
                p for p in self._all_processes
                if query in p.name.lower() or query in str(p.pid)
            ]
        self._populate_table()

    def _sort_by_cpu(self):
        self._filtered_processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        self._populate_table()

    def _sort_by_mem(self):
        self._filtered_processes.sort(key=lambda p: p.memory_used_bytes, reverse=True)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._filtered_processes))
        for row, p in enumerate(self._filtered_processes):
            # PID
            item_pid = QTableWidgetItem(str(p.pid))
            item_pid.setTextAlignment(Qt.AlignCenter)
            item_pid.setForeground(Qt.cyan)
            self.table.setItem(row, 0, item_pid)

            # Name
            item_name = QTableWidgetItem(p.name)
            self.table.setItem(row, 1, item_name)

            # CPU
            item_cpu = QTableWidgetItem(f"{p.cpu_percent:.1f}%")
            item_cpu.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if p.cpu_percent >= 50.0:
                item_cpu.setForeground(Qt.red)
            elif p.cpu_percent >= 20.0:
                item_cpu.setForeground(Qt.yellow)
            self.table.setItem(row, 2, item_cpu)

            # RAM %
            item_ram = QTableWidgetItem(f"{p.memory_percent:.1f}%")
            item_ram.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, item_ram)

            # RAM MB
            mb_used = p.memory_used_bytes / (1024 * 1024)
            item_mb = QTableWidgetItem(f"{mb_used:.1f} MB")
            item_mb.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, item_mb)

            # Status
            item_status = QTableWidgetItem(p.status)
            item_status.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, item_status)

            # User
            user_str = p.username or "System"
            item_user = QTableWidgetItem(user_str)
            self.table.setItem(row, 6, item_user)

    def _on_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < len(self._filtered_processes):
            p = self._filtered_processes[row]
            mb = p.memory_used_bytes / (1024 * 1024)
            self.detail_lbl.setText(
                f"<b>Selected Process:</b> {p.name} (PID: {p.pid})  |  "
                f"<b>CPU:</b> {p.cpu_percent:.1f}%  |  "
                f"<b>Working Set:</b> {mb:.1f} MB ({p.memory_percent:.1f}%)  |  "
                f"<b>Status:</b> {p.status}  |  "
                f"<b>Security Context:</b> {p.username or 'System'}"
            )
