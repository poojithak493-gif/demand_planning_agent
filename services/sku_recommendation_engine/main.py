import pandas as pd

def sku_recommendation_engine(df: pd.DataFrame, top_n: int = 3):
    """
    Recommend top SKUs per distributor based on sales
    """
    df["sku_name"] = df["sku_name"].str.replace(r"\s+", " ", regex=True)

    required_cols = ["distributor_id", "sku_name", "gross_dispatch_value"]

    for col in required_cols:
        if col not in df.columns:
            raise Exception(f"{col} missing in data")

    grouped = (
        df.groupby(["distributor_id", "sku_name"])["gross_dispatch_value"]
        .sum()
        .reset_index()
    )

    grouped = grouped.sort_values(
        ["distributor_id", "gross_dispatch_value"],
        ascending=[True, False]
    )

    recommendations = grouped.groupby("distributor_id").head(top_n)
    

    return recommendations