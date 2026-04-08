import os
import pandas as pd

# --------------------------------------------------
# 1. Define input and output paths
# --------------------------------------------------
input_file = os.path.join("sample_data", "Primary_Sales.xlsx")
output_folder = os.path.join("sample_data", "cleaned")
output_file = os.path.join(output_folder, "primary_sales_cleaned.xlsx")

# --------------------------------------------------
# 2. Create output folder if it does not exist
# --------------------------------------------------
os.makedirs(output_folder, exist_ok=True)

# --------------------------------------------------
# 3. Load Excel file
# --------------------------------------------------
df = pd.read_excel(input_file)

# --------------------------------------------------
# 4. Print raw data details
# --------------------------------------------------
print("Original shape:", df.shape)
print("Original columns:")
print(df.columns.tolist())

# --------------------------------------------------
# 5. Clean column names
# --------------------------------------------------
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# --------------------------------------------------
# 6. Remove duplicate rows
# --------------------------------------------------
df = df.drop_duplicates()

# --------------------------------------------------
# 7. Remove fully empty rows
# --------------------------------------------------
df = df.dropna(how="all")

# --------------------------------------------------
# 8. Remove extra spaces from text columns
# --------------------------------------------------
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].astype(str).str.strip()

# --------------------------------------------------
# 9. Replace empty-like text values with proper null
# --------------------------------------------------
df = df.replace(["", "nan", "None", "null"], pd.NA)

# --------------------------------------------------
# 10. Convert date column if present
# --------------------------------------------------
if "transaction_date" in df.columns:
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

# --------------------------------------------------
# 11. Convert numeric columns if present
# --------------------------------------------------
numeric_cols = [
    "opening_stock_quantity",
    "remaining_quantity",
    "gross_dispatch_value",
    "tax_amount",
    "unit_base_cost",
    "regional_demand_multiplier"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# --------------------------------------------------
# 12. Fill missing text values
# --------------------------------------------------
text_cols = [
    "sku_name",
    "product_category_snapshot",
    "priority_flag",
    "distribution_channel_type",
    "distributor_priority_tier",
    "mapping_status"
]

for col in text_cols:
    if col in df.columns:
        df[col] = df[col].fillna("Unknown")

# --------------------------------------------------
# 13. Fill missing numeric values
# --------------------------------------------------
for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)

# --------------------------------------------------
# 14. Normalize priority_flag values
# --------------------------------------------------
if "priority_flag" in df.columns:
    df["priority_flag"] = df["priority_flag"].str.title()

# --------------------------------------------------
# 15. Print cleaned data details
# --------------------------------------------------
print("\nCleaned shape:", df.shape)
print("Missing values after cleaning:")
print(df.isnull().sum())

# --------------------------------------------------
# 16. Save cleaned file
# --------------------------------------------------
df.to_excel(output_file, index=False)

print(f"\nCleaned file saved at: {output_file}")

# --------------------------------------------------
# 17. Validation checks
# --------------------------------------------------
print("\n--- VALIDATION CHECKS ---")

# Total records
print("Total records:", len(df))

# Duplicate rows
duplicate_count = df.duplicated().sum()
print("Duplicate rows:", duplicate_count)

# Negative gross dispatch values
if "gross_dispatch_value" in df.columns:
    negative_sales = (df["gross_dispatch_value"] < 0).sum()
    print("Negative sales values:", negative_sales)

# Priority distribution
if "priority_flag" in df.columns:
    print("\nPriority distribution:")
    print(df["priority_flag"].value_counts())

# Unique distributors
if "distributor_id" in df.columns:
    print("\nUnique distributors:", df["distributor_id"].nunique())