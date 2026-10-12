# Smart Computer Health Monitor
### An Intelligent, Explainable Operating-System Resource Monitoring Application

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Database](https://img.shields.io/badge/database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/tests-pytest%2022%2F22%20passed-brightgreen.svg)]()
[![Offline](https://img.shields.io/badge/network-100%25%20Offline-success.svg)]()

---

## 1. Project Overview

**Smart Computer Health Monitor** is an academic desktop application developed for an Operating Systems course. Traditional system monitors (such as Task Manager, Activity Monitor, or `top`) restrict themselves to displaying raw measurements—such as `CPU: 94%` or `RAM: 89%`—leaving users uncertain about what those statistics mean, what OS mechanisms are strained, or what corrective actions are safe.

This application bridges that gap with an **Interpretation Layer** that analyzes live hardware telemetry, isolates resource bottlenecks, evaluates evidence across sampling windows, suppresses transient spikes, and produces plain-language diagnoses alongside actionable, non-destructive advisory recommendations.

---

## 2. Problem Statement

Computer users and system administrators regularly experience desktop stutter, application freeze, or thermal throttling. Standard operating system utilities report numerical counters without context:
- A user seeing 95% CPU cannot distinguish between normal multi-core batch compilation and a hung runaway process.
- High memory occupancy is frequently misidentified as a "memory leak," prompting users to install unverified "cleaner" tools.
- Correlated resource stress (such as concurrent CPU starvation and swap file thrashing) is rarely diagnosed holistically.

---

## 3. The Research Gap

The central research gap addressed by this project is the **lack of an explainability and translation layer** between raw operating system counters and human decision-making. 

```
RAW SYSTEM TELEMETRY (psutil / OS kernel)
                    │
                    ▼
          DATA PROCESSING & TIMING
                    │
                    ▼
         THRESHOLD EVALUATION RULES
                    │
                    ▼
     ┌───────────────────────────────┐
     │   THE INTERPRETATION LAYER    │  <--- Core Contribution
     │  (Evidence, OS Impact, Cause) │
     └───────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
HEALTH SCORE (0-100)     ALERTS & DEDUPLICATION
        │                       │
        └───────────┬───────────┘
                    ▼
       SMART RECOMMENDATION ENGINE
                    │
                    ▼
    SQLITE PERSISTENCE & VISUAL DASHBOARD
```

---

## 4. Uniqueness of the Interpretation Layer

The Interpretation Layer answers five fundamental diagnostic questions:
1. **What is happening to my computer?** (Detects elevated demand vs. safe baselines)
2. **Which resource is experiencing a problem?** (Isolates CPU, RAM, Disk, or Battery)
3. **What evidence supports this assessment?** (Provides quantitative samples, duration, and top contributing processes)
4. **What might be contributing to the problem?** (Formulates plausible hypotheses without claiming correlation proves causation)
5. **What action should I take next?** (Provides non-destructive, safe steps to restore performance)

### Epistemic Integrity
The application **never** equates high resource usage with malware or hardware failure. Heavy computational workloads (such as 3D rendering, machine learning inference, or video transcoding) legitimately utilize 100% of CPU capacity.

---

## 5. Key Features

- **Real-Time Telemetry:** Continuous sampling of CPU utilization, logical core distribution, RAM allocations, disk storage usage, disk I/O throughput rates, and battery state.
- **Explainable Health Score (0–100):** Deterministic, rule-based indicator with transparent penalties for CPU contention, RAM pressure, storage exhaustion, and battery drain.
- **Process Explorer:** Real-time process inspection with live search, sorting by CPU/Memory, security context detection, and handling of transient process terminations (`NoSuchProcess`, `AccessDenied`).
- **Explainable Insights (9-Point Framework):** Detection, observed metrics, OS importance, evidence breakdown, possible factors, confidence level, user action, verification step, and expandable raw JSON evidence.
- **Intelligent Alert Lifecycle:** Automated deduplication, cooldown timers, severity escalations (Warning → Critical), acknowledgement tracking, and recovery resolution.
- **Performance History & Multi-Window Analysis:** Real-time embedded Matplotlib dark charts supporting 15m, 1h, 6h, and 24h horizons with statistical summaries (peak, average, min).
- **Advisory Recommendations:** Actionable recommendations with priority rankings and safety warnings against deleting unknown system files or terminating OS services.
- **Report Generation:** Generates comprehensive PDF diagnostic reports via ReportLab and CSV exports of historical telemetry.
- **Local Persistence & Privacy:** 100% offline; all data stored in local SQLite; zero telemetry uploaded to external servers.

---

## 6. Architecture & Modular Design

```
smart-computer-health-monitor/
├── main.py                     # Application entry point & Qt event loop
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
│
├── src/
│   ├── app.py                  # Controller & background QThread worker
│   ├── config.py               # MonitorSettings dataclass & validation
│   │
│   ├── monitoring/
│   │   ├── system_monitor.py   # Non-blocking psutil hardware sampler
│   │   ├── process_monitor.py  # Safe process inspection & lifecycle handling
│   │   └── platform_info.py    # Hardware and OS platform metadata
│   │
│   ├── analysis/
│   │   ├── interpretation_engine.py  # The Interpretation Layer
│   │   ├── health_score.py           # Deterministic 0-100 health score
│   │   ├── recommendation_engine.py  # Actionable advisory recommendations
│   │   └── threshold_rules.py        # Pure threshold validation functions
│   │
│   ├── alerts/
│   │   └── alert_manager.py    # Alert deduplication & lifecycle manager
│   │
│   ├── database/
│   │   ├── db_manager.py       # Thread-safe SQLite database manager
│   │   └── schema.py           # Schema definitions and indexes
│   │
│   ├── history/
│   │   └── history_service.py  # Time-window querying & statistical aggregations
│   │
│   ├── reports/
│   │   └── report_exporter.py  # CSV & ReportLab PDF report generation
│   │
│   └── ui/
│       ├── main_window.py      # QMainWindow with persistent sidebar
│       ├── styles.qss          # Modern Dark Navy design system stylesheet
│       ├── components/
│       │   ├── stat_card.py    # Resource card with live sparkline
│       │   ├── mini_chart.py   # QPainter high-performance live sparkline
│       │   ├── status_badge.py # Styled pill badge
│       │   ├── insight_card.py # 9-point explainable diagnosis card
│       │   └── recommendation_card.py # Actionable advisory card
│       └── pages/
│           ├── overview_page.py         # Summary dashboard & health score
│           ├── resource_monitor_page.py # In-depth CPU/RAM/Disk I/O view
│           ├── process_explorer_page.py # Process table & inspector
│           ├── health_insights_page.py  # Active explainable diagnoses
│           ├── alerts_page.py           # Alert lifecycle & resolution table
│           ├── history_page.py          # Historical charts & metrics
│           ├── recommendations_page.py  # Advisory guidance checklist
│           ├── settings_page.py         # Configuration & threshold tuning
│           └── about_page.py            # Academic background & specs
│
├── tests/
│   ├── test_health_score.py         # Health score model & clamp tests
│   ├── test_interpretation.py       # Spike suppression & evidence tests
│   ├── test_recommendations.py      # Recommendation mapping tests
│   ├── test_alert_manager.py        # Deduplication & escalation tests
│   ├── test_database.py             # SQLite CRUD & migrations tests
│   ├── test_process_monitor.py      # Process error handling tests
│   └── test_reports_and_config.py   # Config validation & PDF tests
│
└── data/
    └── .gitkeep                     # Local SQLite database storage
```

---

## 7. Technology Stack

- **Language:** Python 3.11+
- **Telemetry Engine:** `psutil>=5.9.0` (non-blocking kernel calls)
- **Desktop Framework:** `PySide6>=6.6.0` (Qt 6 for Python)
- **Data Visualization:** `matplotlib>=3.8.0` & custom `QPainter` sparklines
- **Local Persistence:** SQLite 3 with WAL mode and parameterized queries
- **Document Generation:** `reportlab>=4.0.0`
- **Testing:** `pytest>=7.4.0`

---

## 8. Installation & Setup

### Prerequisites
- Python 3.11 or newer installed on the system.

### Windows (PowerShell)
```powershell
# 1. Clone or navigate to the project directory
cd d:\project

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 4. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux / macOS (Bash)
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 9. Running the Application

Ensure the virtual environment is activated, then run:

```powershell
python main.py
```

The application will launch in dark navy mode, start telemetry monitoring at the configured sampling cadence (default: 2.0s), and display live hardware statistics.

---

## 10. Running the Automated Tests

The test suite includes 22 unit and integration tests that mock system hardware to ensure reproducibility across developer environments:

```powershell
python -m pytest -v
```

Expected output:
```
tests/test_alert_manager.py::test_alert_suppression_and_escalation PASSED
tests/test_alert_manager.py::test_alert_acknowledgement_and_manual_resolve PASSED
tests/test_database.py::test_db_init_and_metrics_crud PASSED
tests/test_database.py::test_process_snapshots_and_insights PASSED
tests/test_database.py::test_settings_persistence PASSED
tests/test_database.py::test_clear_all_history PASSED
tests/test_health_score.py::test_perfect_health_score PASSED
tests/test_health_score.py::test_cpu_warning_and_critical_deductions PASSED
tests/test_health_score.py::test_battery_no_penalty_when_plugged_or_unavailable PASSED
tests/test_health_score.py::test_score_boundaries_clamping PASSED
tests/test_interpretation.py::test_normal_metrics_generate_no_insights PASSED
tests/test_interpretation.py::test_brief_cpu_spike_does_not_trigger_sustained_alert PASSED
tests/test_interpretation.py::test_sustained_cpu_triggers_insight_with_evidence PASSED
tests/test_interpretation.py::test_cpu_recovery_lifecycle PASSED
tests/test_interpretation.py::test_ram_and_disk_insights PASSED
tests/test_interpretation.py::test_combined_cpu_and_ram_condition PASSED
tests/test_process_monitor.py::test_process_disappearing_during_inspection PASSED
tests/test_recommendations.py::test_cpu_and_disk_recommendation_mapping PASSED
tests/test_recommendations.py::test_resolved_insights_do_not_generate_recommendations PASSED
tests/test_reports_and_config.py::test_monitor_settings_validation PASSED
tests/test_reports_and_config.py::test_empty_history_handling PASSED
tests/test_reports_and_config.py::test_csv_and_pdf_report_generation PASSED
============================== 22 passed in 0.75s ==============================
```

---

## 11. Database Schema

Stored locally in `data/health_monitor.db`:

- `system_metrics`: Stores timestamped CPU, frequency, RAM bytes, disk capacity, disk I/O read/write rates, battery state, and health score.
- `process_snapshots`: Stores top process resource usage per sampling window (PID, process name, CPU %, Memory %, status).
- `insights`: Stores explainable diagnostic records (resource, severity, title, observed value, explanation, structured evidence JSON, possible cause, confidence, recommendation, status, timestamps).
- `alerts`: Tracks alert notifications (severity, resource, message, acknowledged status, resolved status).
- `settings`: Key-value configuration pairs.

---

## 12. Health Score Mathematical Formulation

The health score is a deterministic indicator from 0 to 100 calculated as:

$$\text{HealthScore} = \max\left(0, \min\left(100, 100 - \left(\sum \text{Deductions}\right) \times \text{Damper}\right)\right)$$

### Deductions Model:
1. **CPU Deduction (0 to 35 pts):**
   - Below Warning (70%): $0$ pts
   - Warning (70%–90%): Proportional deduction from $5$ to $18$ pts
   - Critical (>90%): Proportional deduction from $18$ to $35$ pts
2. **RAM Deduction (0 to 35 pts):**
   - Below Warning (70%): $0$ pts
   - Warning (70%–85%): Proportional deduction from $5$ to $18$ pts
   - Critical (>85%): Proportional deduction from $18$ to $35$ pts
3. **Disk Capacity Deduction (0 to 20 pts):**
   - Below Warning (70%): $0$ pts
   - Warning (70%–90%): Proportional deduction from $4$ to $12$ pts
   - Critical (>90%): Proportional deduction from $12$ to $20$ pts
4. **Battery Deduction (0 to 10 pts):**
   - *AC Plugged in or No Battery Sensor:* $0$ pts (no penalty)
   - *Discharging & Warning (<30%):* Proportional deduction up to $7$ pts
   - *Discharging & Critical (<15%):* $10$ pts
5. **Correlation Damper ($0.85$):**
   - When both CPU and RAM are concurrently under heavy load, deductions are scaled by $0.85$ to avoid double-penalizing correlated application workloads.

### Classification Bands:
- **80 – 100:** Excellent
- **60 – 79:** Good
- **40 – 59:** Warning
- **0 – 39:** Critical

---

## 13. Example Interpretation & Recommendation

### Measured System Data:
- RAM Usage: 91.4% (Available: 1.3 GB out of 16.0 GB)
- Top Memory Consumer: `msedge.exe` (2,140 MB RSS)

### Interpretation Output:
- **Title:** High Memory Pressure Detected
- **Observed Measurement:** `91.4% used (1.3 GB free)`
- **Rule Triggered:** `Memory utilization (91.4%) exceeds critical threshold (85.0%)`
- **OS Significance:** High RAM utilization leaves minimal available memory for file caching. The operating system begins swapping inactive virtual memory pages to the disk paging file, leading to disk thrashing and desktop latency.
- **Evidence:** Structured snapshot of top 3 memory-consuming processes.
- **Possible Factor:** `msedge.exe` is maintaining large web application working sets and cached media.
- **Confidence:** `High Confidence (Direct Metric)`
- **Actionable Next Step:** Review active browser tabs and close dormant web applications.
- **Verification:** Monitor RAM utilization in the Performance History tab to confirm memory reclamation.

---

## 14. Academic Limitations

1. **Hardware Bounds:** The monitor operates in user-space via operating system APIs; it cannot diagnose physical hardware silicon degradation or mechanical disk motor issues.
2. **Heuristic Nature:** Warning (70%) and Critical (90%) thresholds are configurable baselines; server and embedded environments may have different operational profiles.
3. **Advisory Scope:** Recommendations are advisory guidelines and do not perform automated file deletion or process killing.
4. **Platform Availability:** Battery metrics are automatically marked unavailable when running on desktop workstations or virtual machines.

---

## 15. Future Enhancements

- Network socket attribution to map high bandwidth processes to network sockets.
- GPU utilization monitoring via NVML or DirectX hardware counters where supported.
- Linux `systemd` cgroup hierarchy inspection for containerized environments.
- Automated baseline calibration adapting thresholds based on weekly usage patterns.
