from fastapi import APIRouter, HTTPException

from app.schemas.distributor_schema import (
    DistributorContextResponse,
    SKURecommendationResponse,
)
from app.services.distributor_service import DistributorService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/v1/distributors", tags=["Distributors"])

distributor_service = DistributorService()
recommendation_service = RecommendationService()


@router.get("/{distributor_id}/context", response_model=DistributorContextResponse)
def get_distributor_context(distributor_id: str):
    try:
        return distributor_service.get_distributor_context(distributor_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")


@router.get(
    "/{distributor_id}/sku-recommendations",
    response_model=SKURecommendationResponse,
)
def get_sku_recommendations(distributor_id: str):
    try:
        return recommendation_service.get_sku_recommendations(distributor_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")