from temporalio import activity

from app.services.distributor_service import DistributorService
from app.services.email_payload_service import EmailPayloadService
from app.services.recommendation_service import RecommendationService
from app.services.reply_processing_service import ReplyProcessingService


@activity.defn
def fetch_distributor_context_activity(distributor_code: str):
    service = DistributorService()
    return service.get_distributor_context(distributor_code)


@activity.defn
def graph_recommendation_activity(distributor_code: str):
    service = RecommendationService()
    return service.get_sku_recommendations(distributor_code)


@activity.defn
def build_email_activity(distributor_code: str):
    service = EmailPayloadService()
    return service.build_email_payload(distributor_code)


@activity.defn
def send_email_activity(distributor_code: str):
    service = EmailPayloadService()
    return service.send_email_payload(distributor_code)


@activity.defn
def process_reply_activity(
    distributor_code: str,
    email_body: str,
    from_email: str | None = None,
    subject: str | None = None,
    confirmed_by: str | None = None,
    notes: str | None = None,
    received_at: str | None = None,
):
    service = ReplyProcessingService()
    return service.process_reply(
        distributor_code=distributor_code,
        email_body=email_body,
        from_email=from_email,
        subject=subject,
        confirmed_by=confirmed_by,
        notes=notes,
        received_at=received_at,
    )
