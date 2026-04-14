from app.services.resend_client import ResendEmailService


class SendDemandEmailService:
    """
    Sends the demand planning email to the distributor using Resend.

    Input:
        distributor_context: dict (from FetchDistributorContextService)
        email_payload: dict (from BuildDemandEmailService)

    Output:
        Resend API response
    """

    def __init__(self):
        self.email_service = ResendEmailService()

    def execute(self, distributor_context: dict, email_payload: dict):

        distributor_email = distributor_context.get("email")

        if not distributor_email:
            raise ValueError("Distributor email not found in context")

        subject = email_payload.get("subject")
        body = email_payload.get("body")

        if not subject or not body:
            raise ValueError("Email payload missing subject or body")

        response = self.email_service.send_email(
            to_email=distributor_email,
            subject=subject,
            body=body
        )

        return {
            "status": "EMAIL_SENT",
            "distributor_id": distributor_context.get("distributor_id"),
            "email": distributor_email,
            "resend_response": response
        }