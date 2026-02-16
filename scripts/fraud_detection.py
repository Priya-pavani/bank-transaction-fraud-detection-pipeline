import pandas as pd
from datetime import datetime, timedelta


def fraud_rules(gold_current_df: pd.DataFrame, batch_id: str):
    alerts = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Rule 1: High amount
    high_amt = gold_current_df[gold_current_df["amount"] > 200000]
    for _, row in high_amt.iterrows():
        alerts.append({
            "txn_id": row["txn_id"],
            "account_id": row["account_id"],
            "txn_timestamp": row["txn_timestamp"],
            "amount": row["amount"],
            "fraud_type": "RULE_BASED",
            "fraud_rule": "HIGH_AMOUNT_TXN",
            "fraud_score": 90,
            "alert_time": now,
            "batch_id": batch_id
        })

    # Rule 2: Too many txns in short time (5 txns in 10 minutes)
    gold_current_df["txn_timestamp"] = pd.to_datetime(gold_current_df["txn_timestamp"])
    gold_current_df = gold_current_df.sort_values(["account_id", "txn_timestamp"])

    for acc, group in gold_current_df.groupby("account_id"):
        times = group["txn_timestamp"].tolist()
        for i in range(len(times)):
            window_end = times[i] + timedelta(minutes=10)
            count = sum((t >= times[i]) and (t <= window_end) for t in times)
            if count >= 5:
                suspicious_txns = group[(group["txn_timestamp"] >= times[i]) & (group["txn_timestamp"] <= window_end)]
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

    # Anomaly rule: amount > avg + 3*std
    stats = gold_current_df.groupby("account_id")["amount"].agg(["mean", "std"]).reset_index()
    merged = gold_current_df.merge(stats, on="account_id", how="left")

    anomaly_df = merged[merged["amount"] > (merged["mean"] + 3 * merged["std"].fillna(0))]

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

    alerts_df = pd.DataFrame(alerts).drop_duplicates(subset=["txn_id", "fraud_rule"])
    return alerts_df
