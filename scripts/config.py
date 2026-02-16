import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "database", "bank_fraud.db")

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CORRECTED_DIR = os.path.join(BASE_DIR, "data", "corrected")
