import pandas as pd
from sqlalchemy import text

from app.core.constants import NEW_PRODUCTS_CSV_FILE
from app.core.database import SessionLocal


class LoadSKUsFromCSVService:
    def execute(self, csv_file: str = NEW_PRODUCTS_CSV_FILE) -> dict:
        df = pd.read_csv(csv_file, header=2)
        df = df.dropna(how="all").copy()
        df.columns = [str(column).strip() for column in df.columns]
        df = df.fillna("")

        required_columns = ["SKU ID", "SKU Name", "Category"]
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns in products CSV: {missing_columns}")

        insert_query = text(
            """
            INSERT INTO skus (
                sku_code,
                sku_name,
                category,
                unit_of_measure,
                is_active
            )
            VALUES (
                :sku_code,
                :sku_name,
                :category,
                'units',
                TRUE
            )
            ON CONFLICT (sku_code) DO NOTHING
            """
        )

        inserted_rows = 0
        with SessionLocal() as session:
            for _, row in df.iterrows():
                sku_code = str(row.get("SKU ID", "")).strip().upper()
                sku_name = str(row.get("SKU Name", "")).strip()
                category = str(row.get("Category", "")).strip() or None

                if not sku_code or not sku_name:
                    continue

                result = session.execute(
                    insert_query,
                    {
                        "sku_code": sku_code,
                        "sku_name": sku_name,
                        "category": category,
                    },
                )
                inserted_rows += result.rowcount or 0

            session.commit()

        return {
            "loaded": True,
            "inserted_rows": inserted_rows,
            "csv_file": csv_file,
        }
