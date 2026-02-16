import pandas as pd
import hashlib
from datetime import datetime


def hash_record(row: dict):
    key = f"{row['account_id']}|{row['txn_timestamp']}|{row['amount']}|{row['channel']}|{row['merchant_id']}|{row['location']}|{row['status']}|{row['device_id']}"
    return hashlib.md5(key.encode()).hexdigest()


def scd2_merge(silver_df: pd.DataFrame, gold_df: pd.DataFrame, batch_id: str):
    inserted = 0
    updated = 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if gold_df.empty:
        gold_df = pd.DataFrame(columns=[
            "txn_id", "account_id", "txn_timestamp", "amount", "currency", "txn_type",
            "channel", "merchant_id", "location", "status", "device_id",
            "record_hash", "is_current", "effective_from", "effective_to", "batch_id"
        ])

    new_gold_rows = []

    gold_current = gold_df[gold_df["is_current"] == "Y"].copy()

    for _, row in silver_df.iterrows():
        txn_id = row["txn_id"]
        rec_hash = hash_record(row.to_dict())

        existing = gold_current[gold_current["txn_id"] == txn_id]

        if existing.empty:
            inserted += 1
            new_gold_rows.append({
                **row.to_dict(),
                "record_hash": rec_hash,
                "is_current": "Y",
                "effective_from": now,
                "effective_to": None,
                "batch_id": batch_id
            })
        else:
            old_hash = existing.iloc[0]["record_hash"]

            if old_hash != rec_hash:
                updated += 1
                # expire old record
                gold_df.loc[(gold_df["txn_id"] == txn_id) & (gold_df["is_current"] == "Y"), "is_current"] = "N"
                gold_df.loc[(gold_df["txn_id"] == txn_id) & (gold_df["is_current"] == "N") & (gold_df["effective_to"].isna()), "effective_to"] = now

                new_gold_rows.append({
                    **row.to_dict(),
                    "record_hash": rec_hash,
                    "is_current": "Y",
                    "effective_from": now,
                    "effective_to": None,
                    "batch_id": batch_id
                })

    if new_gold_rows:
        gold_df = pd.concat([gold_df, pd.DataFrame(new_gold_rows)], ignore_index=True)

    return gold_df, inserted, updated
