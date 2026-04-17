from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.controllers.postal_webhook_controller import router as postal_webhook_router
from app.services.postal_client import PostalClient

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# Register Postal webhook routes
app.include_router(postal_webhook_router)


@app.get("/")
def root():
    return {
        "message": "API is running",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/send-email/{email}")
def send_email(email: str):
    try:
        postal_client = PostalClient()

        response = postal_client.send_email(
            to_email=email,
            subject="Demand Planning Test Email",
            plain_body=f"Hello {email}, this is a test email from Demand Planning Agent.",
            html_body=f"<p>Hello {email}, this is a test email from Demand Planning Agent 🚀</p>",
        )

        return {
            "status": "success",
            "provider": "postal",
            "response": response,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {exc}")