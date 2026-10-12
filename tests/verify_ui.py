"""
Verification script for UI instantiation and page navigation.
"""

import sys
import os

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use offscreen platform for headless execution verification
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from src.app import AppController
from src.ui.main_window import MainWindow


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    controller = AppController()
    # Disable auto start during quick test to prevent background loop collision
    controller.settings.auto_start_monitoring = False

    window = MainWindow(controller)
    print("MainWindow instantiated successfully.")

    for i in range(9):
        window.switch_page(i)
        print(f"Switched to page index {i} successfully.")

    window.close()
    print("All UI pages verified successfully!")


if __name__ == "__main__":
    main()
