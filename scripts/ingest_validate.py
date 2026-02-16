import pandas as pd
from datetime import datetime
import json


def validate_transactions(df: pd.DataFrame):
    valid_rows = []
    reject_rows = []

    allowed_channels = {"UPI", "CARD", "ATM", "NETBANKING"}
    allowed_status = {"SUCCESS", "FAILED"}
    allowed_type = {"DEBIT", "CREDIT"}

    for _, row in df.iterrows():
        errors = []

        if pd.isna(row.get("txn_id")):
            errors.append("txn_id is null")

        if pd.isna(row.get("account_id")):
            errors.append("account_id is null")

        if pd.isna(row.get("txn_timestamp")):
            errors.append("txn_timestamp is null")

        if pd.isna(row.get("amount")) or float(row.get("amount")) <= 0:
            errors.append("invalid amount")

        if row.get("channel") not in allowed_channels:
            errors.append("invalid channel")

        if row.get("status") not in allowed_status:
            errors.append("invalid status")

        if row.get("txn_type") not in allowed_type:
            errors.append("invalid txn_type")

        if errors:
            reject_rows.append({
                "txn_id": row.get("txn_id"),
                "raw_record": json.dumps(row.to_dict()),
                "error_reason": "; ".join(errors),
                "rejected_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            valid_rows.append(row.to_dict())

    valid_df = pd.DataFrame(valid_rows)
    reject_df = pd.DataFrame(reject_rows)

    return valid_df, reject_df
