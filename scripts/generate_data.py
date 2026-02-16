import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from config import RAW_DIR, CORRECTED_DIR


def generate_transactions(n=20000, day_offset=0):
    np.random.seed(42 + day_offset)

    base_date = datetime.now() - timedelta(days=day_offset)

    txn_ids = [f"TXN{day_offset}{i:06d}" for i in range(n)]
    account_ids = [f"ACC{np.random.randint(1000, 9999)}" for _ in range(n)]

    timestamps = [
        (base_date - timedelta(minutes=np.random.randint(0, 1440))).strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(n)
    ]

    amounts = np.random.exponential(scale=5000, size=n).round(2)
    amounts = np.clip(amounts, 10, 300000)

    channels = np.random.choice(["UPI", "CARD", "ATM", "NETBANKING"], size=n)
    txn_type = np.random.choice(["DEBIT", "CREDIT"], size=n, p=[0.8, 0.2])
    status = np.random.choice(["SUCCESS", "FAILED"], size=n, p=[0.95, 0.05])
    currency = ["INR"] * n

    merchant_ids = [f"M{np.random.randint(100, 999)}" for _ in range(n)]
    location = np.random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"], size=n)
    device_id = [f"D{np.random.randint(10000, 99999)}" for _ in range(n)]

    df = pd.DataFrame({
        "txn_id": txn_ids,
        "account_id": account_ids,
        "txn_timestamp": timestamps,
        "amount": amounts,
        "currency": currency,
        "txn_type": txn_type,
        "channel": channels,
        "merchant_id": merchant_ids,
        "location": location,
        "status": status,
        "device_id": device_id
    })

    # Inject some fraud patterns
    fraud_idx = np.random.choice(df.index, size=int(n * 0.01), replace=False)
    df.loc[fraud_idx, "amount"] = np.random.randint(150000, 300000, size=len(fraud_idx))

    # Inject some invalid rows (bad data)
    bad_idx = np.random.choice(df.index, size=int(n * 0.005), replace=False)
    df.loc[bad_idx, "txn_id"] = None

    return df


def create_corrected_file(original_df: pd.DataFrame, corrections=300):
    df_corr = original_df.copy()

    # Pick random transactions and change amount/status
    idx = np.random.choice(df_corr.index, size=corrections, replace=False)

    df_corr.loc[idx, "amount"] = df_corr.loc[idx, "amount"] * np.random.uniform(1.5, 3.0, size=corrections)
    df_corr.loc[idx, "amount"] = df_corr.loc[idx, "amount"].round(2)

    df_corr.loc[idx, "status"] = "SUCCESS"

    # only keep corrected records subset
    df_corr = df_corr.loc[idx]

    return df_corr


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CORRECTED_DIR, exist_ok=True)

    day1 = generate_transactions(n=20000, day_offset=1)
    raw_file = os.path.join(RAW_DIR, "transactions_day1.csv")
    day1.to_csv(raw_file, index=False)

    corrected = create_corrected_file(day1, corrections=400)
    corr_file = os.path.join(CORRECTED_DIR, "corrected_transactions_day1.csv")
    corrected.to_csv(corr_file, index=False)

    print("Generated:")
    print(raw_file)
    print(corr_file)


if __name__ == "__main__":
    main()
