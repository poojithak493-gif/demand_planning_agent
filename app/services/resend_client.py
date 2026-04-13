import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")


class ResendClient:
    def send_email(self, to_email: str, subject: str, body: str) -> dict:
        # --- IMPROVEMENT: Wrapped in try/except with structured error response ---
        # Old version had no error handling — any Resend API failure (bad key,
        # rate limit, network error) would raise an uncaught exception and crash
        # the calling service with no useful context about what failed or why.
        #
        # New version:
        #   1. Catches all exceptions and returns a structured dict instead of raising.
        #   2. Validates that required env vars are set before even attempting the call.
        #   3. Returns a consistent shape { success, message_id, error } so callers
        #      can check outcome without wrapping every call in their own try/except.

        from_email = os.getenv("RESEND_FROM_EMAIL")

        # Guard: fail fast with a clear message if env is misconfigured
        if not resend.api_key:
            return {
                "success": False,
                "message_id": None,
                "error": "RESEND_API_KEY environment variable is not set."
            }
        if not from_email:
            return {
                "success": False,
                "message_id": None,
                "error": "RESEND_FROM_EMAIL environment variable is not set."
            }

        try:
            response = resend.Emails.send({
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": body
            })
            return {
                "success": True,
                "message_id": response.get("id"),
                "error": None
            }

        except Exception as e:
            # Log and return structured failure — don't re-raise
            print(f"[ERROR] Resend email to {to_email} failed: {e}")
            return {
                "success": False,
                "message_id": None,
                "error": str(e)
            }