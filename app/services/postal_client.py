import requests
from typing import Optional, Dict, Any

from app.core.config import settings


class PostalClient:
    """
    Handles email sending via Postal.

    Supports:
    - Simulation mode (for local testing)
    - Real Postal API mode (for production)
    """

    def __init__(self):
        self.base_url = settings.POSTAL_BASE_URL.rstrip("/")
        self.server_key = settings.POSTAL_SERVER_KEY
        self.from_email = settings.POSTAL_FROM_EMAIL

        # Toggle this flag for simulation
        self.simulation_mode = True   # 👉 set False in production

    def send_email(
        self,
        to_email: str,
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None,
    ) -> Dict[str, Any]:

        # =========================
        # SIMULATION MODE
        # =========================
        if self.simulation_mode:
            print("\n📧 SIMULATED EMAIL SEND")
            print("To:", to_email)
            print("Subject:", subject)
            print("Body:", plain_body)

            return {
                "status": "SIMULATED",
                "message_id": "demo123"
            }

        # =========================
        # REAL POSTAL API MODE
        # =========================
        url = f"{self.base_url}/api/v1/send/message"

        payload = {
            "from": self.from_email,
            "to": to_email,
            "subject": subject,
            "plain_body": plain_body,
        }

        if html_body:
            payload["html_body"] = html_body

        headers = {
            "X-Server-API-Key": self.server_key,
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        response.raise_for_status()

        return response.json()