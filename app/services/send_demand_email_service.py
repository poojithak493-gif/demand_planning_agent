from app.integrations.resend_client import ResendClient


class SendDemandEmailService:
    def __init__(self):
        self.client = ResendClient()

    def execute(self, to_email: str, subject: str, body: str):
        return self.client.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )