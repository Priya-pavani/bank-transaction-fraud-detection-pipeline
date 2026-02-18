# Bank Transaction Fraud Detection Pipeline (DE Project)

This project is an end-to-end **Data Engineering + Analytics** pipeline that simulates a **Bank Transaction Fraud Detection System**.

It includes:
- Synthetic transaction data generation (with fraud patterns + bad data)
- Batch ingestion into SQLite
- Data quality checks and rejected records logging
- Bronze → Silver → Gold processing layers
- SCD Type 2 implementation in Gold layer
- Rule-based + anomaly-based fraud detection
- Audit logging for each pipeline batch run
- Streamlit dashboard for monitoring fraud + data quality + pipeline health


---

## 📌 Project Architecture

### **1. Data Generation**
A synthetic dataset is generated daily with:
- Normal transactions
- Fraud transactions (different fraud patterns)
- Bad records (missing/invalid values)

Generated Files:
- `data/raw/transactions_dayX.csv`
- `data/corrected/corrected_transactions_dayX.csv`


### **2. Data Pipeline Flow**
The pipeline follows the **Medallion Architecture**:

| Layer | Purpose |
|------|---------|
| Bronze | Raw ingested data |
| Silver | Cleaned + validated transactions |
| Gold | Current + historical SCD2 transactions |
| Fraud Alerts | Fraud detection output |
| Rejects | Invalid records rejected during DQ checks |


---

## 🔍 Data Quality Checks Implemented

Records are rejected and moved into `rejected_transactions` table if they fail any of these checks:

### **Null Checks**
- `txn_id` is NULL
- `account_id` is NULL
- `txn_timestamp` is NULL
- `merchant_id` is NULL

### **Amount Checks**
- Amount is 0
- Amount is negative

### **Domain / Allowed Values Checks**
- Invalid `channel` (must be UPI, CARD, ATM, NETBANKING)
- Invalid `status` (must be SUCCESS or FAILED)
- Currency must be INR

### **Duplicate Checks**
- Duplicate `txn_id` values


---

## 🚨 Fraud Detection Rules Implemented

Fraud detection runs on the **Gold current dataset** (`is_current='Y'`) and creates records in `fraud_alerts`.

### Rule 1: High Amount Fraud
- Trigger: amount > 200000

### Rule 2: Rapid Transaction Burst
- Trigger: ≥ 5 transactions within 10 minutes for same account

### Rule 3: Amount Spike Anomaly
- Trigger: amount > mean + 3*std for that account

### Rule 4: Multiple Locations Fraud
- Trigger: same account has transactions from multiple cities in short duration

### Rule 5: Multiple Failed Attempts Fraud
- Trigger: 3+ FAILED followed by SUCCESS

### Rule 6: Shared Device Fraud
- Trigger: same device_id used across multiple accounts


---

## 🧾 Audit Logging

Each pipeline run writes into `batch_audit_log`:
- batch_id
- start_time
- end_time
- status (SUCCESS/FAILED)
- total_records_ingested
- total_rejected
- total_fraud_alerts


---

## 🏗️ Database Tables Created

### Core Tables
- `bronze_transactions`
- `silver_transactions`
- `gold_transactions_scd2`

### Monitoring Tables
- `rejected_transactions`
- `fraud_alerts`
- `batch_audit_log`


---

## ▶️ How to Run the Project

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Generate sample transaction files
```bash
python scripts/generate_data.py
```

### Step 3: Run the pipeline
```bash
python scripts/run_pipeline.py
```

### Step 4: Run the dashboard
```bash
python -m streamlit run dashboard/app.py
```


---

## 📊 Streamlit Dashboard Features

### Fraud Overview Tab
- Total transactions
- Total fraud alerts
- Fraud rate
- Fraud trend over time
- Sample fraud alerts

### Fraud Rules Tab
- Fraud alerts grouped by rule

### Data Quality Tab
- Rejected record count by error reason

### Audit Logs Tab
- Batch history + pipeline health
- Gold sample (SCD2)


---



## 🚀 Possible Enhancements
- Add Airflow orchestration
- Add Kafka streaming ingestion
- Deploy dashboard to cloud
- Use Spark instead of Pandas for large-scale processing
- Add ML model fraud scoring


<img width="1262" height="814" alt="image" src="https://github.com/user-attachments/assets/c8a17e99-b247-49a1-8f4a-767a00f30d52" />
<img width="1366" height="767" alt="image" src="https://github.com/user-attachments/assets/12211c46-04cd-4989-8109-fd0b609d4210" />
<img width="746" height="784" alt="image" src="https://github.com/user-attachments/assets/e9e99e04-f8d9-4f0f-8fe8-c820874713f4" />



---

## 🗂️ Database Schema (Simplified)

```mermaid
erDiagram
    batch_audit_log ||--o{ bronze_transactions : "tracks"
    batch_audit_log ||--o{ silver_transactions : "tracks"
    batch_audit_log ||--o{ rejected_transactions : "tracks"
    batch_audit_log ||--o{ fraud_alerts : "tracks"

    bronze_transactions ||--o| silver_transactions : "cleaned_into"
    bronze_transactions ||--o| rejected_transactions : "rejects_to"

    silver_transactions ||--o{ gold_transactions_scd2 : "merged_into"
    gold_transactions_scd2 ||--o{ fraud_alerts : "generates"

    bronze_transactions {
        string txn_id
        string account_id
        string txn_timestamp
        float amount
        string status
        string file_name
        string batch_id
    }

    silver_transactions {
        string txn_id
        string account_id
        string txn_timestamp
        float amount
        string status
        string batch_id
    }

    gold_transactions_scd2 {
        int surrogate_key
        string txn_id
        string record_hash
        string is_current
        string effective_from
        string effective_to
        string batch_id
    }

    fraud_alerts {
        int alert_id
        string txn_id
        string fraud_rule
        int fraud_score
        string batch_id
    }

    rejected_transactions {
        int reject_id
        string txn_id
        string error_reason
        string batch_id
    }

    batch_audit_log {
        string batch_id
        int total_records
        int rejected_records
        int fraud_flagged
        string status
    }

```

---

