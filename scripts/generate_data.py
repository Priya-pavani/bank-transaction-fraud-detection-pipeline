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
    location = np.random.choice(
        ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"],
        size=n
    )
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

    # =====================================================
    # Inject FRAUD PATTERNS (for fraud dashboard variety)
    # =====================================================

    # A) High amount fraud
    fraud_idx = np.random.choice(df.index, size=int(n * 0.005), replace=False)
    df.loc[fraud_idx, "amount"] = np.random.randint(150000, 300000, size=len(fraud_idx))

    # B) Rapid burst fraud (same account multiple txns in 10 mins)
    burst_accounts = np.random.choice(df["account_id"].dropna().unique(), size=10, replace=False)

    for acc in burst_accounts:
        acc_df = df[df["account_id"] == acc]
        sample_size = min(8, len(acc_df))

        if sample_size < 2:
            continue

        burst_rows = acc_df.sample(sample_size, replace=False).index
        base_time = datetime.now() - timedelta(minutes=np.random.randint(0, 120))

        df.loc[burst_rows, "txn_timestamp"] = [
            (base_time + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")
            for i in range(sample_size)
        ]
        df.loc[burst_rows, "amount"] = np.random.randint(3000, 15000, size=sample_size)
        df.loc[burst_rows, "channel"] = "UPI"

    # C) Multiple locations fraud (same account different cities in short time)
    loc_accounts = np.random.choice(df["account_id"].dropna().unique(), size=12, replace=False)
    cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"]

    for acc in loc_accounts:
        acc_df = df[df["account_id"] == acc]
        sample_size = min(5, len(acc_df))

        if sample_size < 2:
            continue

        idxs = acc_df.sample(sample_size, replace=False).index
        df.loc[idxs, "location"] = np.random.choice(cities, size=sample_size, replace=False)

    # D) Failed attempts then success fraud
    fail_accounts = np.random.choice(df["account_id"].dropna().unique(), size=12, replace=False)

    for acc in fail_accounts:
        acc_df = df[df["account_id"] == acc]
        sample_size = min(5, len(acc_df))

        if sample_size < 2:
            continue

        idxs = acc_df.sample(sample_size, replace=False).index.tolist()

        if len(idxs) >= 4:
            df.loc[idxs[:4], "status"] = "FAILED"
            df.loc[idxs[4:], "status"] = "SUCCESS"
        else:
            df.loc[idxs[:-1], "status"] = "FAILED"
            df.loc[idxs[-1:], "status"] = "SUCCESS"

        df.loc[idxs, "amount"] = np.random.randint(1000, 8000, size=len(idxs))
        df.loc[idxs, "channel"] = "CARD"

    # E) Same device used across multiple accounts (device fraud)
    shared_device = f"D{np.random.randint(10000, 99999)}"
    device_fraud_rows = np.random.choice(df.index, size=20, replace=False)
    df.loc[device_fraud_rows, "device_id"] = shared_device

    # F) Merchant fraud: many txns to same merchant
    merchant_fraud_merchant = f"M{np.random.randint(100, 999)}"
    merchant_fraud_rows = np.random.choice(df.index, size=30, replace=False)
    df.loc[merchant_fraud_rows, "merchant_id"] = merchant_fraud_merchant
    df.loc[merchant_fraud_rows, "amount"] = np.random.randint(50000, 120000, size=30)

    # =====================================================
    # Inject BAD DATA (for data quality dashboard variety)
    # =====================================================

    # 1) Missing txn_id
    bad_idx1 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx1, "txn_id"] = None

    # 2) Missing account_id
    bad_idx2 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx2, "account_id"] = None

    # 3) Missing timestamp
    bad_idx3 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx3, "txn_timestamp"] = None

    # 4) Negative amount
    bad_idx4 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx4, "amount"] = -1 * np.random.randint(10, 5000, size=len(bad_idx4))

    # 5) Zero amount
    bad_idx5 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx5, "amount"] = 0

    # 6) Invalid channel
    bad_idx6 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx6, "channel"] = "INVALID_CHANNEL"

    # 7) Invalid status
    bad_idx7 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx7, "status"] = "UNKNOWN"

    # 8) Wrong currency
    bad_idx8 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx8, "currency"] = "USD"

    # 9) Duplicate txn_id
    dup_idx = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[dup_idx, "txn_id"] = df.loc[dup_idx, "txn_id"].iloc[0]

    # 10) Missing merchant_id
    bad_idx9 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx9, "merchant_id"] = None

    # 11) Invalid txn_type
    bad_idx10 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx10, "txn_type"] = "INVALID_TYPE"

    # 12) Invalid timestamp format
    bad_idx11 = np.random.choice(df.index, size=int(n * 0.002), replace=False)
    df.loc[bad_idx11, "txn_timestamp"] = "NOT_A_DATE"

    return df


def create_corrected_file(original_df: pd.DataFrame, corrections=300):
    df_corr = original_df.copy()

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
