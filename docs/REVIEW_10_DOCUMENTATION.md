# Review 10: Project Documentation

## Smart Computer Health Monitor

**Student:** Ajay  
**Course / Subject:** Operating Systems  
**Review:** 10  
**Document type:** Complete project documentation

---

## 1. Abstract

Smart Computer Health Monitor is a privacy-preserving desktop application for monitoring and explaining computer resource health. It collects operating-system telemetry, persists historical observations locally, evaluates configurable thresholds, and presents human-readable diagnoses and recommendations.

The project addresses a limitation of conventional monitoring tools: a raw value such as `95% CPU` describes utilization but does not explain whether the condition is temporary, which process contributes to it, why it matters to the operating system, or what a user can safely do next.

## 2. Objectives

The project objectives are:

1. Collect live system measurements without blocking the user interface.
2. Display CPU, memory, disk, I/O, battery, and process information.
3. Convert measurements into a transparent health score from 0 to 100.
4. Detect sustained resource pressure rather than overreacting to one sample.
5. Explain findings using evidence, OS impact, confidence, and verification steps.
6. Provide non-destructive recommendations.
7. Preserve history locally for trend analysis and reports.
8. Keep all monitoring data offline and under the user's control.

## 3. Scope

### Included

- Windows and other platforms supported by `psutil`
- CPU, RAM, disk capacity, disk I/O, and battery monitoring
- Process inspection and resource sorting
- Rule-based analysis and recommendations
- Alert lifecycle management
- SQLite persistence
- History charts and statistical summaries
- CSV and PDF report generation
- Automated unit and integration tests

### Not included

- Malware detection
- Physical hardware-failure diagnosis
- Automatic process termination
- Automatic file deletion or system cleanup
- Cloud telemetry or remote account synchronization
- Guaranteed GPU metrics on every machine

## 4. System Architecture

```text
                         +----------------------+
                         |      PySide6 UI      |
                         | pages, cards, charts |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         |   App Controller      |
                         | worker thread/timing  |
                         +----------+-----------+
                                    |
             +----------------------+----------------------+
             |                      |                      |
   +---------v---------+  +---------v---------+  +---------v---------+
   | System Monitor    |  | Process Monitor   |  | Platform Info     |
   | psutil telemetry  |  | safe inspection   |  | OS/hardware data  |
   +---------+---------+  +---------+---------+  +-------------------+
             |                      |
             +----------------------v----------------------+
                         | Analysis layer        |
                         | thresholds, score,    |
                         | interpretation,       |
                         | recommendations       |
                         +-----------+------------+
                                     |
                  +------------------v------------------+
                  | Alerts, history, database, reports  |
                  | SQLite | CSV | PDF                   |
                  +-------------------------------------+
```

## 5. Module Description

### 5.1 Application and configuration

- [`main.py`](../main.py) creates the `QApplication`, configures logging, loads the stylesheet, and opens the main window.
- [`src/app.py`](../src/app.py) coordinates monitoring work and UI updates.
- [`src/config.py`](../src/config.py) stores validated monitoring settings and paths.

### 5.2 Monitoring

- [`src/monitoring/system_monitor.py`](../src/monitoring/system_monitor.py) captures CPU, per-core CPU, RAM, disk, disk I/O, and battery readings.
- [`src/monitoring/process_monitor.py`](../src/monitoring/process_monitor.py) reads process information while handling processes that terminate or deny access during inspection.
- [`src/monitoring/platform_info.py`](../src/monitoring/platform_info.py) provides operating-system and hardware metadata.

### 5.3 Analysis

- [`src/analysis/threshold_rules.py`](../src/analysis/threshold_rules.py) contains reusable threshold checks.
- [`src/analysis/health_score.py`](../src/analysis/health_score.py) calculates a deterministic score and deduction breakdown.
- [`src/analysis/interpretation_engine.py`](../src/analysis/interpretation_engine.py) evaluates evidence across samples and creates explainable insights.
- [`src/analysis/recommendation_engine.py`](../src/analysis/recommendation_engine.py) maps active insights to safe recommendations.

### 5.4 Persistence and reporting

- [`src/database/schema.py`](../src/database/schema.py) defines SQLite tables and indexes.
- [`src/database/db_manager.py`](../src/database/db_manager.py) performs database operations.
- [`src/history/history_service.py`](../src/history/history_service.py) queries time windows and computes summaries.
- [`src/reports/report_exporter.py`](../src/reports/report_exporter.py) creates CSV and PDF reports.

### 5.5 User interface

- [`src/ui/main_window.py`](../src/ui/main_window.py) provides the shell and navigation.
- `src/ui/pages/` contains Overview, History, Insights, Recommendations, Process Explorer, Resource Monitor, Settings, and About pages.
- `src/ui/components/` contains reusable cards, badges, charts, and insight widgets.
- [`src/ui/styles.qss`](../src/ui/styles.qss) defines the dark-navy visual system.

## 6. Data Flow

1. The monitoring worker requests a new reading at the configured interval.
2. `SystemMonitor` obtains values from `psutil`.
3. The reading is evaluated by threshold rules and the health-score calculator.
4. The interpretation engine compares current and recent samples.
5. New or recovered insights are passed to the alert manager.
6. Metrics, process snapshots, insights, and alerts are stored in SQLite.
7. The controller emits updated data to the UI.
8. History pages query stored data for charts and summaries.
9. The report exporter produces CSV/PDF output on request.

## 7. Health Score

The score is bounded to the interval 0–100:

```text
score = clamp(100 - total_deductions, 0, 100)
```

Deductions are calculated independently for:

- CPU pressure: maximum 35 points
- RAM pressure: maximum 35 points
- Disk capacity pressure: maximum 20 points
- Low battery while discharging: maximum 10 points

When CPU and RAM are both heavily penalized, a correlation damper reduces double-counting of one workload's related effects. Battery is not penalized when the device is plugged in or when no battery sensor is available.

Classification:

| Score | Classification |
|---:|---|
| 80–100 | Excellent |
| 60–79 | Good |
| 40–59 | Warning |
| 0–39 | Critical |

## 8. Interpretation and Alert Lifecycle

The interpretation engine distinguishes a short spike from sustained pressure. An insight can move through the following lifecycle:

```text
inactive -> active -> acknowledged -> resolved
             |          |
             +----------+
               escalation / recovery
```

Alerts are deduplicated and subject to cooldowns. This keeps the dashboard useful instead of repeatedly notifying the user about the same sample.

Each insight is designed around a nine-point explanation:

1. Detection
2. Observed measurement
3. OS significance
4. Evidence breakdown
5. Possible contributing factors
6. Confidence
7. Recommended action
8. Verification step
9. Raw structured evidence

## 9. Database Design

The local database is `data/health_monitor.db`.

| Table | Purpose |
|---|---|
| `system_metrics` | Timestamped resource measurements and health scores |
| `process_snapshots` | Top process usage captured during sampling |
| `insights` | Explainable diagnoses and their lifecycle status |
| `alerts` | Notification, acknowledgement, escalation, and resolution state |
| `settings` | Persisted key-value configuration |

The database is local-only. No network connection is required for monitoring, analysis, storage, or reporting.

## 10. Installation

### Windows PowerShell

```powershell
cd Smart-Computer-Health-Monitor
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux / macOS

```bash
cd Smart-Computer-Health-Monitor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 11. Running the Application

```powershell
python main.py
```

The application starts the dashboard, begins sampling at the configured cadence, and writes application events to `health_monitor.log`.

## 12. Testing and Quality Assurance

Run:

```powershell
python -m pytest -v
```

The tests cover calculations, threshold behavior, persistence, process lifecycle edge cases, alert state transitions, recommendations, configuration validation, and report generation. Hardware-dependent behavior is mocked where appropriate so results are reproducible.

## 13. Privacy and Safety

- Measurements remain on the local computer.
- The application does not upload telemetry.
- Recommendations are advisory and non-destructive.
- The application does not kill processes or delete files.
- High usage is not treated as proof of malware or hardware failure.
- Missing platform sensors are represented explicitly as unavailable.

## 14. Limitations

1. User-space APIs cannot diagnose every physical hardware fault.
2. Thresholds are configurable heuristics and may need tuning for servers or specialized workloads.
3. Battery information is unavailable on desktops and some virtual machines.
4. GPU and network attribution are outside the current core scope.
5. A recommendation indicates a safe next step; it does not guarantee a specific root cause.

## 15. Future Enhancements

- GPU utilization through NVML or DirectX counters
- Network socket attribution by process
- Baseline calibration from long-term usage history
- Linux cgroup/container resource views
- Optional authenticated remote dashboards
- Additional export formats and scheduled reports

## 16. Conclusion

Smart Computer Health Monitor combines operating-system telemetry, explainable rules, persistence, and a user-focused interface into one offline diagnostic tool. Its primary value is not only measuring resource use, but also making the measurement understandable, evidence-based, and actionable without taking unsafe automated actions.

