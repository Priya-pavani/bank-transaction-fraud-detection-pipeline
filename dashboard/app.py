import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "bank_fraud.db")

st.set_page_config(page_title="Fraud Dashboard", layout="wide")


def load_df(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


st.title("🏦 Bank Transaction Fraud Monitoring Dashboard")

alerts = load_df("SELECT * FROM fraud_alerts")
gold = load_df("SELECT * FROM gold_transactions_scd2 WHERE is_current='Y'")
rejects = load_df("SELECT * FROM rejected_transactions")
audit = load_df("SELECT * FROM batch_audit_log ORDER BY start_time DESC")


# convert timestamps
if not alerts.empty:
    alerts["txn_timestamp"] = pd.to_datetime(alerts["txn_timestamp"], errors="coerce")
    alerts["alert_time"] = pd.to_datetime(alerts["alert_time"], errors="coerce")

if not gold.empty:
    gold["txn_timestamp"] = pd.to_datetime(gold["txn_timestamp"], errors="coerce")


tab1, tab2, tab3, tab4 = st.tabs(["Fraud Overview", "Fraud Rules", "Data Quality", "Audit Logs"])


# ---------------------------------------------------
# TAB 1
# ---------------------------------------------------
with tab1:
    st.subheader("Fraud Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Current Transactions", len(gold))
    col2.metric("Total Fraud Alerts", len(alerts))

    if len(gold) > 0:
        col3.metric("Fraud Rate (%)", round((len(alerts) / len(gold)) * 100, 2))
    else:
        col3.metric("Fraud Rate (%)", 0)

    st.divider()

    if alerts.empty:
        st.warning("No fraud alerts found in the database.")
    else:
        # ------------------------------
        # filters
        # ------------------------------
        st.markdown("### Filters")

        rule_list = sorted(alerts["fraud_rule"].dropna().unique().tolist())
        rule_list.insert(0, "ALL")

        selected_rule = st.selectbox("Fraud Rule", rule_list)

        filtered_alerts = alerts.copy()
        if selected_rule != "ALL":
            filtered_alerts = filtered_alerts[filtered_alerts["fraud_rule"] == selected_rule]

        # date range filter
        min_date = filtered_alerts["txn_timestamp"].min()
        max_date = filtered_alerts["txn_timestamp"].max()

        if pd.isna(min_date) or pd.isna(max_date):
            st.info("Transaction timestamps missing for fraud alerts.")
        else:
            start_date, end_date = st.date_input(
                "Transaction Date Range",
                value=(min_date.date(), max_date.date())
            )

            filtered_alerts = filtered_alerts[
                (filtered_alerts["txn_timestamp"].dt.date >= start_date) &
                (filtered_alerts["txn_timestamp"].dt.date <= end_date)
            ]

        st.divider()

        # ------------------------------
        # trend plot (by txn_timestamp)
        # ------------------------------
        if not filtered_alerts.empty:
            filtered_alerts["date"] = filtered_alerts["txn_timestamp"].dt.date
            trend = filtered_alerts.groupby("date").size().reset_index(name="fraud_alerts")

            fig, ax = plt.subplots()
            ax.plot(trend["date"], trend["fraud_alerts"], marker="o")
            ax.set_title("Fraud Alerts Trend (by Transaction Date)")
            ax.set_xlabel("Date")
            ax.set_ylabel("Fraud Alerts")
            plt.xticks(rotation=45)

            st.pyplot(fig)

        st.markdown("### Fraud Alerts Sample")
        st.dataframe(filtered_alerts.sort_values("txn_timestamp", ascending=False).head(50))


# ---------------------------------------------------
# TAB 2
# ---------------------------------------------------
with tab2:
    st.subheader("Fraud Rule Distribution")

    if alerts.empty:
        st.warning("No fraud alerts found.")
    else:
        rule_counts = alerts.groupby("fraud_rule").size().reset_index(name="count")
        rule_counts = rule_counts.sort_values("count", ascending=False)

        fig, ax = plt.subplots()
        ax.bar(rule_counts["fraud_rule"], rule_counts["count"])
        ax.set_title("Fraud Alerts by Rule")
        ax.set_xlabel("Fraud Rule")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45)

        st.pyplot(fig)

        st.dataframe(rule_counts)


# ---------------------------------------------------
# TAB 3
# ---------------------------------------------------
with tab3:
    st.subheader("Rejected Transactions (Data Quality Issues)")

    if rejects.empty:
        st.success("No rejected records found. Data quality looks clean.")
    else:
        reject_summary = rejects.groupby("error_reason").size().reset_index(name="count")
        reject_summary = reject_summary.sort_values("count", ascending=False)

        fig, ax = plt.subplots()
        ax.barh(reject_summary["error_reason"], reject_summary["count"])
        ax.set_title("Rejected Records by Reason")
        ax.set_xlabel("Count")

        st.pyplot(fig)

        st.markdown("### Reject Summary")
        st.dataframe(reject_summary)

        st.markdown("### Sample Rejected Records")
        st.dataframe(rejects.head(50))


# ---------------------------------------------------
# TAB 4
# ---------------------------------------------------
with tab4:
    st.subheader("Batch Audit Logs")

    if audit.empty:
        st.warning("No batch audit logs found.")
    else:
        st.dataframe(audit)

    st.divider()

    st.subheader("Gold Table Sample (SCD2)")

    if gold.empty:
        st.warning("Gold table is empty.")
    else:
        sample_gold = gold[["txn_id", "account_id", "amount", "status", "channel", "location", "txn_timestamp"]].head(50)
        st.dataframe(sample_gold)
