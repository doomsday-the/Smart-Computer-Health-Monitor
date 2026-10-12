"""
SQLite Database schema definitions and migrations.
"""

SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS schema_info (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
    cpu_frequency REAL,
    ram_percent REAL NOT NULL,
    ram_used_bytes INTEGER NOT NULL,
    ram_available_bytes INTEGER NOT NULL,
    ram_total_bytes INTEGER NOT NULL,
    disk_used_bytes INTEGER,
    disk_free_bytes INTEGER,
    disk_total_bytes INTEGER,
    disk_percent REAL,
    disk_read_bytes INTEGER,
    disk_write_bytes INTEGER,
    battery_percent REAL,
    battery_plugged INTEGER,
    health_score REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp);

CREATE TABLE IF NOT EXISTS process_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    cpu_percent REAL,
    memory_percent REAL,
    memory_used_bytes INTEGER,
    process_status TEXT
);

CREATE INDEX IF NOT EXISTS idx_process_timestamp ON process_snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_process_name ON process_snapshots(process_name);

CREATE TABLE IF NOT EXISTS insights (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resource TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    observed_value TEXT,
    rule_triggered TEXT,
    explanation TEXT NOT NULL,
    evidence_json TEXT,
    possible_cause TEXT,
    confidence_label TEXT,
    recommendation TEXT,
    status TEXT NOT NULL,
    resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_insights_status ON insights(status);
CREATE INDEX IF NOT EXISTS idx_insights_updated ON insights(updated_at);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    resource TEXT NOT NULL,
    message TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    resolved INTEGER DEFAULT 0,
    FOREIGN KEY(insight_id) REFERENCES insights(id)
);

CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(acknowledged, resolved);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
