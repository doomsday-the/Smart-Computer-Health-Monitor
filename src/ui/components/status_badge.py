"""
Status Badge component.
Displays styled pill badges for health, severity, and process states.
"""

from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    """Pill badge with severity-based coloring."""

    def __init__(self, text: str = "Healthy", severity: str = "healthy", parent=None):
        super().__init__(text, parent)
        self.set_severity(severity, text)

    def set_severity(self, severity: str, text: str = None):
        if text:
            self.setText(text)
        sev = severity.lower()
        if sev in ("healthy", "excellent", "normal"):
            self.setProperty("class", "badge-healthy")
        elif sev in ("good", "info"):
            self.setProperty("class", "badge-good")
        elif sev in ("warning", "elevated"):
            self.setProperty("class", "badge-warning")
        elif sev in ("critical", "danger", "error"):
            self.setProperty("class", "badge-critical")
        else:
            self.setProperty("class", "badge-good")

        self.style().unpolish(self)
        self.style().polish(self)
