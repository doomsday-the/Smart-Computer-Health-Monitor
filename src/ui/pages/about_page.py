"""
About Project Page.
Presents academic background, operating systems research problem statement,
the interpretation layer gap, methodology, platform details, and scientific limitations.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout
)
from src.monitoring.platform_info import PlatformInfo


class AboutPage(QWidget):
    """Academic project documentation and platform information view."""

    def __init__(self, platform_info: PlatformInfo, parent=None):
        super().__init__(parent)
        self.plat = platform_info

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        title_box = QVBoxLayout()
        title_lbl = QLabel("About Project & Research Specification")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #F8FAFC;")
        sub_lbl = QLabel("Smart Computer Health Monitor — Academic Operating Systems Capstone")
        sub_lbl.setStyleSheet("color: #38BDF8; font-size: 13px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        main_layout.addLayout(title_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 1. Project Overview & Problem Statement
        p1 = self._create_section(
            title="1. Problem Statement & Research Domain",
            body=(
                "<b>Project Domain:</b> Operating Systems and System Performance Monitoring.<br/><br/>"
                "<b>Problem:</b> Users and administrators frequently encounter sluggish performance, input stutter, "
                "or thermal throttling, yet traditional operating system monitors (such as Task Manager or top) "
                "merely display raw quantitative counters (e.g., CPU 94%, RAM 88%). Ordinary users cannot readily determine "
                "which underlying OS mechanism is stressed (such as thread queue starvation or virtual memory paging thrash), "
                "nor do standard utilities explain what actionable steps are safe to undertake."
            )
        )
        layout.addWidget(p1)

        # 2. Research Contribution: The Interpretation Layer
        p2 = self._create_section(
            title="2. The Central Research Contribution: The Interpretation Layer",
            body=(
                "Traditional monitoring stops at data collection. This project implements a dedicated "
                "<b>Interpretation Layer</b> governed by an evidence-based five-question framework:<br/>"
                "<ol style='color: #E2E8F0;'>"
                "<li><b>What is happening to my computer?</b> (Abnormal resource detection)</li>"
                "<li><b>Which resource is experiencing a problem?</b> (Subsystem isolation)</li>"
                "<li><b>What evidence supports this assessment?</b> (Direct empirical measurements & persistence)</li>"
                "<li><b>What might be contributing to the problem?</b> (Plausible factors distinguished from proof)</li>"
                "<li><b>What safe action should I take next?</b> (Targeted, non-destructive advisory steps)</li>"
                "</ol>"
                "<b>Epistemic Rule:</b> The engine strictly enforces that correlation does not prove causation; "
                "heavy resource utilization is recognized as legitimate compute demand rather than assumed software corruption."
            )
        )
        layout.addWidget(p2)

        # 3. Hardware & Operating System Environment
        p3 = QFrame()
        p3.setProperty("class", "card-panel")
        p3_lay = QVBoxLayout(p3)
        p3_title = QLabel("3. Detected Hardware & Operating System Platform")
        p3_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;")
        p3_lay.addWidget(p3_title)

        grid = QGridLayout()
        grid.setSpacing(10)
        total_ram_gb = self.plat.total_ram_bytes / (1024 ** 3)
        batt_str = "Present & Monitored" if self.plat.has_battery else "Not Present (Desktop / VM)"

        items = [
            ("Operating System:", f"{self.plat.os_name} {self.plat.os_release} (Build {self.plat.os_version})"),
            ("CPU Architecture:", f"{self.plat.architecture} ({self.plat.processor_name})"),
            ("Core Topography:", f"{self.plat.physical_cores} Physical Cores / {self.plat.logical_cores} Logical Threads"),
            ("Physical RAM:", f"{total_ram_gb:.2f} GB Total Installed Capacity"),
            ("Battery Hardware:", batt_str),
            ("Storage Partitions:", f"{len(self.plat.partitions)} active volume mountpoints detected")
        ]

        for i, (k, v) in enumerate(items):
            r = i // 2
            c = (i % 2) * 2
            lbl_k = QLabel(k)
            lbl_k.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px;")
            lbl_v = QLabel(v)
            lbl_v.setStyleSheet("color: #F8FAFC; font-size: 12px;")
            grid.addWidget(lbl_k, r, c)
            grid.addWidget(lbl_v, r, c + 1)

        p3_lay.addLayout(grid)
        layout.addWidget(p3)

        # 4. Limitations & Academic Disclaimers
        p4 = self._create_section(
            title="4. Limitations & Academic Disclaimers",
            body=(
                "<ul>"
                "<li><b>Diagnostic Bounds:</b> The application evaluates operating system resource states and cannot diagnose deep hardware circuitry faults (such as VRM degradation or mechanical bearing failure).</li>"
                "<li><b>Heuristic Nature:</b> Resource warning and critical thresholds are configurable heuristic baselines.</li>"
                "<li><b>Advisory Recommendations:</b> Recommendations are advisory guidelines and do not guarantee hardware repair.</li>"
                "<li><b>Safety & Integrity:</b> High CPU or memory utilization alone does not indicate malicious code. No automatic file deletions or process terminations are performed.</li>"
                "</ul>"
            )
        )
        layout.addWidget(p4)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_section(self, title: str, body: str) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "card-panel")
        lay = QVBoxLayout(frame)
        lay.setSpacing(8)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC;")
        b_lbl = QLabel(body)
        b_lbl.setStyleSheet("color: #CBD5E1; font-size: 13px; line-height: 1.5;")
        b_lbl.setWordWrap(True)
        lay.addWidget(t_lbl)
        lay.addWidget(b_lbl)
        return frame
