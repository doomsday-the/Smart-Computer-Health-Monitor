"""
Mini Chart and Sparkline component.
Uses QPainter for high-performance, real-time live graphs without flickering or UI lag.
"""

from collections import deque
from typing import List, Optional
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
from PySide6.QtWidgets import QWidget


class RealtimeSparkline(QWidget):
    """Smooth real-time line chart with gradient fill and auto-scaling."""

    def __init__(
        self,
        max_points: int = 40,
        color_hex: str = "#4F8CFF",
        min_y: float = 0.0,
        max_y: float = 100.0,
        parent=None
    ):
        super().__init__(parent)
        self.max_points = max_points
        self.color = QColor(color_hex)
        self.min_y = min_y
        self.max_y = max_y
        self.data: deque[float] = deque(maxlen=max_points)
        self.setMinimumHeight(45)

    def add_point(self, value: float):
        self.data.append(value)
        self.update()

    def set_data(self, points: List[float]):
        self.data = deque(points, maxlen=self.max_points)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if len(self.data) < 2:
            painter.setPen(QColor("#334155"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Waiting for data...")
            return

        pts = list(self.data)
        n = len(pts)
        dx = w / (self.max_points - 1)

        # Draw subtle background grid lines (25%, 50%, 75%)
        painter.setPen(QPen(QColor("#1E2E48"), 1, Qt.DotLine))
        for pct in (0.25, 0.5, 0.75):
            y_line = h * (1.0 - pct)
            painter.drawLine(0, int(y_line), w, int(y_line))

        # Calculate coordinates
        path = QPainterPath()
        points: List[QPointF] = []
        start_idx = self.max_points - n

        for i, val in enumerate(pts):
            val_clamped = max(self.min_y, min(self.max_y, val))
            ratio = (val_clamped - self.min_y) / max(1.0, (self.max_y - self.min_y))
            x = (start_idx + i) * dx
            y = h - (ratio * (h - 8)) - 4
            points.append(QPointF(x, y))

        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)

        # Create gradient fill under curve
        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), h)
        fill_path.lineTo(points[0].x(), h)
        fill_path.closeSubpath()

        gradient = QLinearGradient(0, 0, 0, h)
        c_top = QColor(self.color)
        c_top.setAlpha(60)
        c_bot = QColor(self.color)
        c_bot.setAlpha(0)
        gradient.setColorAt(0, c_top)
        gradient.setColorAt(1, c_bot)

        painter.fillPath(fill_path, QBrush(gradient))

        # Draw stroke
        pen = QPen(self.color, 2)
        painter.setPen(pen)
        painter.drawPath(path)

        # Highlight latest point
        latest = points[-1]
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawEllipse(latest, 3, 3)
