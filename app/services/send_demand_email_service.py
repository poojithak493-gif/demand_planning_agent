from app.services.resend_client import ResendClient


class SendDemandEmailService:
    def __init__(self) -> None:
        self.resend_client = ResendClient()

    def execute(self, to_email: str, subject: str, body: str) -> dict:
        return self.resend_client.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
        )
