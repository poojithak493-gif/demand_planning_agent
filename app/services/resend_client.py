import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


class ResendEmailService:

    def send_email(self, to_email: str, subject: str, body: str):
        response = resend.Emails.send({
            "from": os.getenv("RESEND_FROM_EMAIL"),
            "to": [to_email],
            "subject": subject,
            "text": body
        })

        return response