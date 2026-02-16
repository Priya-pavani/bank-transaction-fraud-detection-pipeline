-- ============================
-- BRONZE (RAW LANDING)
-- ============================
CREATE TABLE IF NOT EXISTS bronze_transactions (
    txn_id TEXT,
    account_id TEXT,
    txn_timestamp TEXT,
    amount REAL,
    currency TEXT,
    txn_type TEXT,
    channel TEXT,
    merchant_id TEXT,
    location TEXT,
    status TEXT,
    device_id TEXT,
    file_name TEXT,
    batch_id TEXT,
    ingestion_time TEXT
);

-- ============================
-- REJECTS TABLE
-- ============================
CREATE TABLE IF NOT EXISTS rejected_transactions (
    reject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT,
    raw_record TEXT,
    error_reason TEXT,
    batch_id TEXT,
    rejected_time TEXT
);

-- ============================
-- SILVER (CLEANED / VALIDATED)
-- ============================
CREATE TABLE IF NOT EXISTS silver_transactions (
    txn_id TEXT,
    account_id TEXT,
    txn_timestamp TEXT,
    amount REAL,
    currency TEXT,
    txn_type TEXT,
    channel TEXT,
    merchant_id TEXT,
    location TEXT,
    status TEXT,
    device_id TEXT,
    batch_id TEXT
);

-- ============================
-- GOLD (FINAL SCD2 TABLE)
-- ============================
CREATE TABLE IF NOT EXISTS gold_transactions_scd2 (
    surrogate_key INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT,
    account_id TEXT,
    txn_timestamp TEXT,
    amount REAL,
    currency TEXT,
    txn_type TEXT,
    channel TEXT,
    merchant_id TEXT,
    location TEXT,
    status TEXT,
    device_id TEXT,
    record_hash TEXT,
    is_current TEXT,
    effective_from TEXT,
    effective_to TEXT,
    batch_id TEXT
);

-- ============================
-- FRAUD ALERTS TABLE
-- ============================
CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT,
    account_id TEXT,
    txn_timestamp TEXT,
    amount REAL,
    fraud_type TEXT,
    fraud_rule TEXT,
    fraud_score INTEGER,
    alert_time TEXT,
    batch_id TEXT
);

-- ============================
-- AUDIT LOG TABLE
-- ============================
CREATE TABLE IF NOT EXISTS batch_audit_log (
    batch_id TEXT PRIMARY KEY,
    file_name TEXT,
    start_time TEXT,
    end_time TEXT,
    total_records INTEGER,
    valid_records INTEGER,
    rejected_records INTEGER,
    inserted_records INTEGER,
    updated_records INTEGER,
    fraud_flagged INTEGER,
    status TEXT,
    error_message TEXT
);
