import os
import pandas as pd

INPUT_FILE = os.path.join("sample_data", "Primary_Sales.xlsx")
OUTPUT_FOLDER = os.path.join("sample_data", "cleaned")
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "primary_sales_cleaned.xlsx")


def load_primary_sales() -> pd.DataFrame:
    return pd.read_excel(INPUT_FILE)


def save_cleaned_primary_sales(df: pd.DataFrame) -> str:
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    df.to_excel(OUTPUT_FILE, index=False)
    return OUTPUT_FILE