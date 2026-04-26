from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.repositories.primary_sales_repository import (
    load_primary_sales,
    save_cleaned_primary_sales,
)

from app.services.validation_service import (
    clean_primary_sales,
    validate_primary_sales,
)

router = APIRouter(prefix="/validation", tags=["Validation"])


@router.get("/primary-sales")
def run_primary_sales_validation(
    db: Annotated[Session, Depends(get_db)]
):
    file_path = "sample_data/Primary_Sales.xlsx"

    raw_df = load_primary_sales(file_path)

    cleaned_df = clean_primary_sales(raw_df)

    cleaned_file_path = save_cleaned_primary_sales(
        db,
        cleaned_df
    )

    validation_results = validate_primary_sales(cleaned_df)

    validation_results["cleaned_file_path"] = cleaned_file_path

    return validation_results