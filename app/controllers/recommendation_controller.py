from fastapi import APIRouter

from app.services.distributor_service import DistributorService
from app.services.email_payload_service import EmailPayloadService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

distributor_service = DistributorService()
recommendation_service = RecommendationService()
email_payload_service = EmailPayloadService()


@router.get("/{distributor_id}")
def get_recommendations(distributor_id: str):
    context = distributor_service.get_distributor_context(distributor_id)
    recommendations = recommendation_service.get_sku_recommendations(distributor_id)
    email_payload = email_payload_service.build_email_payload(distributor_id)

    return {
        "context": context,
        "recommendations": recommendations.get("recommended_skus", []),
        "email_preview": {
            "subject": email_payload["email_subject"],
            "body": email_payload["email_body"],
        },
    }
