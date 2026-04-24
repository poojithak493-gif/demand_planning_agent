from temporalio import activity

from app.core.database import SessionLocal
from app.services.fetch_distributor_context_service import FetchDistributorContextService
from app.services.sku_recommendation_service import SKURecommendationService
from app.services.build_demand_email_service import build_demand_email
from app.services.send_demand_email_service import send_email


@activity.defn
def fetch_distributor_context_activity(distributor_id: str):
    db = SessionLocal()
    try:
        service = FetchDistributorContextService(db)
        return service.execute(distributor_id)
    finally:
        db.close()


@activity.defn
def graph_recommendation_activity(distributor_id: str):
    service = SKURecommendationService()
    return service.execute(distributor_id)


@activity.defn
def build_email_activity(context: dict, recommendations: dict):
    distributor_id = context.get("distributor_id")
    distributor_email = context.get("email")
    return build_demand_email(distributor_id, distributor_email)


@activity.defn
def send_email_activity(to_email: str, email_payload: dict):
    return send_email(
        to_email=to_email,
        subject=email_payload["subject"],
        body=email_payload["body"]
    )