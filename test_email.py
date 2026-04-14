from app.services.resend_client import ResendEmailService

service = ResendEmailService()

response = service.send_email(
    to_email="revanbejagam@gmail.com",  # replace with your email
    subject="Test Email from Demand Planning AI",
    body="This is a test email to verify Resend setup."
)

print(response)