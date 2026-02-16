import os
import pandas as pd
from datetime import datetime
import uuid

from config import RAW_DIR, CORRECTED_DIR
from db_utils import write_df, read_df, execute_sql
from ingest_validate import validate_transactions
from scd2_merge import scd2_merge
from fraud_detection import fraud_rules


def generate_batch_id():
    return str(uuid.uuid4())[:8]


def run_for_file(file_path: str, batch_id: str):
    file_name = os.path.basename(file_path)

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    audit = {
        "batch_id": batch_id,
        "file_name": file_name,
        "start_time": start_time,
        "end_time": None,
        "total_records": 0,
        "valid_records": 0,
        "rejected_records": 0,
        "inserted_records": 0,
        "updated_records": 0,
        "fraud_flagged": 0,
        "status": "RUNNING",
        "error_message": None
    }

    try:
        df = pd.read_csv(file_path)
        audit["total_records"] = len(df)

        ingestion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_bronze = df.copy()
        df_bronze["file_name"] = file_name
        df_bronze["batch_id"] = batch_id
        df_bronze["ingestion_time"] = ingestion_time

        write_df(df_bronze, "bronze_transactions")

        valid_df, reject_df = validate_transactions(df)

        if not reject_df.empty:
            reject_df["batch_id"] = batch_id
            write_df(reject_df, "rejected_transactions")

        if not valid_df.empty:
            valid_df["batch_id"] = batch_id
            write_df(valid_df, "silver_transactions")

        audit["valid_records"] = len(valid_df)
        audit["rejected_records"] = len(reject_df)

        # read current gold table
        gold_df = read_df("SELECT * FROM gold_transactions_scd2")

        gold_updated_df, inserted, updated = scd2_merge(valid_df, gold_df, batch_id)

        # overwrite gold table
        conn_sql = "DELETE FROM gold_transactions_scd2"
        execute_sql(conn_sql)
        write_df(gold_updated_df.drop(columns=["surrogate_key"], errors="ignore"), "gold_transactions_scd2")

        audit["inserted_records"] = inserted
        audit["updated_records"] = updated

        # fraud detection on current gold records only
        gold_current = gold_updated_df[gold_updated_df["is_current"] == "Y"].copy()
        if not gold_current.empty:
            alerts_df = fraud_rules(gold_current, batch_id)
            if not alerts_df.empty:
                write_df(alerts_df, "fraud_alerts")
                audit["fraud_flagged"] = len(alerts_df)

        audit["status"] = "SUCCESS"

    except Exception as e:
        audit["status"] = "FAILED"
        audit["error_message"] = str(e)

    audit["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # write audit (upsert)
    execute_sql(f"DELETE FROM batch_audit_log WHERE batch_id = '{batch_id}'")
    write_df(pd.DataFrame([audit]), "batch_audit_log")


def main():
    raw_file = os.path.join(RAW_DIR, "transactions_day1.csv")
    corrected_file = os.path.join(CORRECTED_DIR, "corrected_transactions_day1.csv")

    print("Running RAW batch ingestion...")
    run_for_file(raw_file, batch_id=generate_batch_id())

    print("Running CORRECTED batch ingestion...")
    run_for_file(corrected_file, batch_id=generate_batch_id())

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
