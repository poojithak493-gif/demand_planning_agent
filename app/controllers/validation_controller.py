from app.repositories.primary_sales_repository import (
    load_primary_sales,
    save_cleaned_primary_sales,

)
from app.services.validation_service import (
    clean_primary_sales,
    validate_primary_sales,
)

from services.sku_recommendation_engine.main import sku_recommendation_engine


def run_primary_sales_validation():
    raw_df = load_primary_sales()
    cleaned_df = clean_primary_sales(raw_df)

    cleaned_file_path = save_cleaned_primary_sales(cleaned_df)

    validation_results = validate_primary_sales(cleaned_df)

    # recm eng
    recommendations = sku_recommendation_engine(cleaned_df)
    validation_results["recommendations"] = recommendations.to_dict(orient="records")

    validation_results["cleaned_file_path"] = cleaned_file_path

    return validation_results