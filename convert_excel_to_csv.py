import pandas as pd

# Input Excel file
excel_file = "sample_data/30_Recommended_New_Products.xlsx"

# Output CSV file
csv_file = "sample_data/products.csv"

# Read Excel
df = pd.read_excel(excel_file)

# Convert to CSV
df.to_csv(csv_file, index=False)

print(f"Successfully converted {excel_file} to {csv_file}")
