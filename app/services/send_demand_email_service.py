from app.services.postal_client import PostalClient


class SendDemandEmailService:
    """
    Sends the demand planning email to the distributor using Postal.

    Input:
        distributor_context: dict (from FetchDistributorContextService)
        email_payload: dict (from BuildDemandEmailService)

    Output:
        Postal API response
    """

    def __init__(self):
        self.email_service = PostalClient()

    def execute(self, distributor_context: dict, email_payload: dict):

        distributor_email = distributor_context.get("email")

        if not distributor_email:
            raise ValueError("Distributor email not found in context")

        subject = email_payload.get("subject")
        body = email_payload.get("body")
        html_body = email_payload.get("html_body")

        if not subject or not body:
            raise ValueError("Email payload missing subject or body")

        response = self.email_service.send_email(
            to_email=distributor_email,
            subject=subject,
            plain_body=body,
            html_body=html_body
        )

        return {
            "status": "EMAIL_SENT",
            "distributor_id": distributor_context.get("distributor_id"),
            "email": distributor_email,
            "postal_response": response
        }