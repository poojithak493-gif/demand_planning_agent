from fastapi import FastAPI
from app.core.config import settings
from app.services.send_demand_email_service import send_email, send_bulk_emails

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)


@app.get("/")
def home():
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION
    }


@app.get("/health")
def health_check():
    return {
        "status": "success",
        "message": "Application startup complete."
    }


@app.get("/send-test")
def send_test():
    return send_email(
        to_email="demo@postal.local",
        subject="Test Email from Demand Planning Agent",
        body="Hello, this is a test email sent from FastAPI using Postal SMTP."
    )


@app.get("/send-bulk")
def send_bulk():
    distributors = [
        {"name": "D01", "email": "rishithareddyc2002@gmail.com"},
        {"name": "D02", "email": "lingaphani21@gmail.com"},
        {"name": "D03", "email": "revanbejagam@gmail.com"},
    ]

    return send_bulk_emails(distributors)