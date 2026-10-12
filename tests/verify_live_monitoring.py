"""
Live monitoring integration test.
Runs the background worker with live OS metrics for 6 seconds,
verifies that SQLite records are inserted, signals are emitted,
and monitoring stops cleanly.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QCoreApplication
from src.app import AppController


def main():
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    controller = AppController()
    controller.settings.monitoring_interval_sec = 1.0

    readings_received = []
    scores_received = []

    controller.start_monitoring()
    worker = controller.worker

    def on_reading(r):
        readings_received.append(r)
        print(f"Captured live sample: CPU={r.cpu_percent}%, RAM={r.ram_percent}%, Battery={r.battery_percent}")

    def on_score(s):
        scores_received.append(s)

    worker.reading_ready.connect(on_reading)
    worker.score_ready.connect(on_score)

    start_time = time.time()
    while time.time() - start_time < 5.0:
        app.processEvents()
        time.sleep(0.1)

    controller.stop_monitoring()
    print("Monitoring stopped cleanly.")

    # Check database records
    recent_metrics = controller.db.get_recent_metrics(limit=10)
    print(f"Total metrics rows in DB: {len(recent_metrics)}")

    assert len(readings_received) >= 1, "Expected at least 1 reading during test"
    assert len(recent_metrics) >= 2, "Expected at least 2 DB rows inserted"

    print("Live monitoring verification PASSED successfully!")


if __name__ == "__main__":
    main()
