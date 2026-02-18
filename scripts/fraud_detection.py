import pandas as pd
from datetime import datetime, timedelta


def fraud_rules(gold_current_df: pd.DataFrame, batch_id: str):
    alerts = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure timestamp column is datetime
    gold_current_df["txn_timestamp"] = pd.to_datetime(gold_current_df["txn_timestamp"], errors="coerce")
    gold_current_df = gold_current_df.dropna(subset=["txn_timestamp"])

    gold_current_df = gold_current_df.sort_values(["account_id", "txn_timestamp"])

    # ======================================================
    # RULE 1: High amount transaction
    # ======================================================
    high_amt = gold_current_df[gold_current_df["amount"] > 200000]
    for _, row in high_amt.iterrows():
        alerts.append({
            "txn_id": row["txn_id"],
            "account_id": row["account_id"],
            "txn_timestamp": row["txn_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "amount": row["amount"],
            "fraud_type": "RULE_BASED",
            "fraud_rule": "HIGH_AMOUNT_TXN",
            "fraud_score": 90,
            "alert_time": now,
            "batch_id": batch_id
        })

    # ======================================================
    # RULE 2: Rapid burst transactions (>=5 txns in 10 mins)
    # ======================================================
    for acc, group in gold_current_df.groupby("account_id"):
        times = group["txn_timestamp"].tolist()

        for i in range(len(times)):
            window_end = times[i] + timedelta(minutes=10)
            count = sum((t >= times[i]) and (t <= window_end) for t in times)

            if count >= 5:
                suspicious_txns = group[
                    (group["txn_timestamp"] >= times[i]) &
                    (group["txn_timestamp"] <= window_end)
                ]

                for _, row in suspicious_txns.iterrows():
                    alerts.append({
                        "txn_id": row["txn_id"],
                        "account_id": row["account_id"],
                        "txn_timestamp": row["txn_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                        "amount": row["amount"],
                        "fraud_type": "RULE_BASED",
                        "fraud_rule": "RAPID_TXN_BURST",
                        "fraud_score": 80,
                        "alert_time": now,
                        "batch_id": batch_id
                    })
                break

    # ======================================================
    # RULE 3: Multiple locations within 1 hour (>=3 cities)
    # ======================================================
    for acc, group in gold_current_df.groupby("account_id"):
        last_1hr = group[group["txn_timestamp"] >= (group["txn_timestamp"].max() - timedelta(hours=1))]

        if last_1hr["location"].nunique() >= 3:
            for _, row in last_1hr.iterrows():
                alerts.append({
                    "txn_id": row["txn_id"],
                    "account_id": row["account_id"],
                    "txn_timestamp": row["txn_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": row["amount"],
                    "fraud_type": "RULE_BASED",
                    "fraud_rule": "MULTI_LOCATION_ACTIVITY",
                    "fraud_score": 75,
                    "alert_time": now,
                    "batch_id": batch_id
                })

    # ======================================================
    # RULE 4: Failed attempts then success pattern
    # (>=4 failed txns in last 30 mins)
    # ======================================================
    for acc, group in gold_current_df.groupby("account_id"):
        last_30 = group[group["txn_timestamp"] >= (group["txn_timestamp"].max() - timedelta(minutes=30))]

        failed_count = (last_30["status"] == "FAILED").sum()
        success_count = (last_30["status"] == "SUCCESS").sum()

        if failed_count >= 4 and success_count >= 1:
            for _, row in last_30.iterrows():
                alerts.append({
                    "txn_id": row["txn_id"],
                    "account_id": row["account_id"],
                    "txn_timestamp": row["txn_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": row["amount"],
                    "fraud_type": "RULE_BASED",
                    "fraud_rule": "FAILED_THEN_SUCCESS_PATTERN",
                    "fraud_score": 85,
                    "alert_time": now,
                    "batch_id": batch_id
                })

    # ======================================================
    # RULE 5: Same device used across multiple accounts
    # (device_id appears for >=5 accounts)
    # ======================================================
    device_counts = gold_current_df.groupby("device_id")["account_id"].nunique().reset_index()
    suspicious_devices = device_counts[device_counts["account_id"] >= 5]["device_id"].tolist()

    device_fraud = gold_current_df[gold_current_df["device_id"].isin(suspicious_devices)]

    for _, row in device_fraud.iterrows():
        alerts.append({
            "txn_id": row["txn_id"],
            "account_id": row["account_id"],
            "txn_timestamp": row["txn_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "amount": row["amount"],
            "fraud_type": "RULE_BASED",
            "fraud_rule": "DEVICE_SHARED_ACROSS_ACCOUNTS",
            "fraud_score": 78,
            "alert_time": now,
            "batch_id": batch_id
        })

    # ======================================================
    # RULE 6: Anomaly detection (amount > mean + 3*std)
    # ======================================================
    stats = gold_current_df.groupby("account_id")["amount"].agg(["mean", "std"]).reset_index()
    merged = gold_current_df.merge(stats, on="account_id", how="left")

    merged["std"] = merged["std"].fillna(0)

    anomaly_df = merged[merged["amount"] > (merged["mean"] + 3 * merged["std"])]

    for _, row in anomaly_df.iterrows():
        alerts.append({
            "txn_id": row["txn_id"],
            "account_id": row["account_id"],
            "txn_timestamp": row["txn_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "amount": row["amount"],
            "fraud_type": "ANOMALY",
            "fraud_rule": "AMOUNT_SPIKE_ANOMALY",
            "fraud_score": 70,
            "alert_time": now,
            "batch_id": batch_id
        })

    alerts_df = pd.DataFrame(alerts)

    if not alerts_df.empty:
        alerts_df = alerts_df.drop_duplicates(subset=["txn_id", "fraud_rule"])

    return alerts_df
