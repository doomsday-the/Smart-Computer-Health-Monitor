"""
Smart Computer Health Monitor.
Main application launcher and desktop interface entry point.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.config import DEFAULT_LOG_PATH, BASE_DIR
from src.app import AppController
from src.ui.main_window import MainWindow


def setup_logging():
    """Configure structured application logging to console and local log file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(DEFAULT_LOG_PATH), encoding="utf-8")
        ]
    )
    logging.info("Starting Smart Computer Health Monitor...")


def load_stylesheet(app: QApplication):
    """Load dark navy QSS stylesheet."""
    qss_path = BASE_DIR / "src" / "ui" / "styles.qss"
    if qss_path.exists():
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
            app.setStyleSheet(stylesheet)
            logging.info("Loaded dark navy QSS stylesheet.")
        except Exception as e:
            logging.warning(f"Could not load stylesheet: {e}")


def main():
    setup_logging()

    # Enable high DPI scaling
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Computer Health Monitor")
    app.setOrganizationName("Operating Systems Research")

    # Load custom modern styles
    load_stylesheet(app)

    # Initialize Controller and Main Window
    controller = AppController()
    window = MainWindow(controller)
    window.show()

    # Enter Qt main event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
