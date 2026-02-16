import sqlite3
import pandas as pd
from config import DB_PATH
print("Using DB:", DB_PATH)


def get_connection():
    return sqlite3.connect(DB_PATH)


def write_df(df: pd.DataFrame, table: str, mode="append"):
    conn = get_connection()
    df.to_sql(table, conn, if_exists=mode, index=False)
    conn.close()


def read_df(query: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def execute_sql(sql: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()
