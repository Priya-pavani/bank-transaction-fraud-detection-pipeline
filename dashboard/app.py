import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "bank_fraud.db")

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")

def load_df(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("🏦 Bank Transaction Fraud Detection Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["Fraud Overview", "Fraud Rules", "Data Quality", "Audit Logs"])

with tab1:
    st.subheader("Fraud Alerts Overview")

    alerts = load_df("SELECT * FROM fraud_alerts")
    gold = load_df("SELECT * FROM gold_transactions_scd2 WHERE is_current='Y'")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Current Transactions", len(gold))
    col2.metric("Total Fraud Alerts", len(alerts))
    col3.metric("Fraud Rate (%)", round((len(alerts)/len(gold))*100, 2) if len(gold) > 0 else 0)

    if not alerts.empty:
        alerts["alert_time"] = pd.to_datetime(alerts["alert_time"])
        alerts["date"] = alerts["alert_time"].dt.date

        trend = alerts.groupby("date").size().reset_index(name="fraud_alerts")

        fig, ax = plt.subplots()
        ax.plot(trend["date"], trend["fraud_alerts"], marker="o")
        ax.set_title("Fraud Alerts Trend")
        ax.set_xlabel("Date")
        ax.set_ylabel("Fraud Alerts")
        st.pyplot(fig)

    st.dataframe(alerts.head(50))

with tab2:
    st.subheader("Fraud Rule Distribution")

    alerts = load_df("SELECT fraud_rule, COUNT(*) as count FROM fraud_alerts GROUP BY fraud_rule")

    if not alerts.empty:
        fig, ax = plt.subplots()
        ax.bar(alerts["fraud_rule"], alerts["count"])
        ax.set_title("Fraud Alerts by Rule")
        ax.set_xlabel("Rule")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    st.dataframe(alerts)

with tab3:
    st.subheader("Rejected Transactions (Data Quality)")

    rejects = load_df("SELECT error_reason, COUNT(*) as count FROM rejected_transactions GROUP BY error_reason")

    if not rejects.empty:
        fig, ax = plt.subplots()
        ax.barh(rejects["error_reason"], rejects["count"])
        ax.set_title("Rejected Records by Reason")
        ax.set_xlabel("Count")
        st.pyplot(fig)

    st.dataframe(rejects)

with tab4:
    st.subheader("Batch Audit Log")

    audit = load_df("SELECT * FROM batch_audit_log ORDER BY start_time DESC")
    st.dataframe(audit)

    st.subheader("Gold Table Sample (SCD2)")
    gold_sample = load_df("SELECT txn_id, account_id, amount, is_current, effective_from, effective_to FROM gold_transactions_scd2 LIMIT 50")
    st.dataframe(gold_sample)
