from app.services.demand_plan_service import DemandPlanService
from app.services.helpers.build_demand_email_service import BuildDemandEmailService
from app.services.helpers.send_mail import send_email


class EmailPayloadService:
    def __init__(self) -> None:
        self.demand_plan_service = DemandPlanService()
        self.build_demand_email_service = BuildDemandEmailService()

    def build_email_payload(self, distributor_code: str) -> dict:
        demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
        distributor = demand_plan["distributor"]
        recommended_skus = demand_plan["recommended_skus"]

        helper_payload = self._build_helper_payload(distributor, recommended_skus)
        email_subject = helper_payload.get(
            "subject",
            self._build_subject(distributor),
        )
        email_body = helper_payload.get(
            "body",
            self._build_body(distributor, recommended_skus),
        )

        return {
            "distributor_code": distributor["distributor_code"],
            "distributor_name": distributor["name"],
            "recipient_email": distributor["email"],
            "email_subject": email_subject,
            "email_body": email_body,
            "recommended_skus": recommended_skus,
        }

    def send_email_payload(
        self,
        distributor_code: str,
        attachment_path: str | None = None,
    ) -> dict:
        email_payload = self.build_email_payload(distributor_code)
        send_result = send_email(
            to_email=email_payload["recipient_email"],
            subject=email_payload["email_subject"],
            body=email_payload["email_body"],
            attachment_path=attachment_path,
        )

        return {
            "distributor_code": distributor_code,
            "recipient_email": email_payload["recipient_email"],
            "email_subject": email_payload["email_subject"],
            "sent": send_result["sent"],
            "attachment_path": attachment_path,
        }

    def _build_helper_payload(self, distributor: dict, recommended_skus: list[dict]) -> dict:
        distributor_context = {
            "distributor_code": distributor["distributor_code"],
            "sku_demand_signals": distributor.get("sku_demand_signals", []),
        }
        recommendation_response = {
            "recommendations": recommended_skus,
        }

        try:
            return self.build_demand_email_service.execute(
                distributor_context,
                recommendation_response,
            )
        except Exception:
            return {}

    @staticmethod
    def _build_subject(distributor: dict) -> str:
        return (
            f"Demand Planning Request for {distributor['name']} "
            f"({distributor['distributor_code']})"
        )

    @staticmethod
    def _build_body(distributor: dict, recommended_skus: list[dict]) -> str:
        body_lines = [
            f"Hello {distributor['name']},",
            "",
            "Please review the recommended SKUs below for the upcoming demand plan.",
            f"Distributor code: {distributor['distributor_code']}",
            "",
        ]

        if recommended_skus:
            for index, sku in enumerate(recommended_skus, start=1):
                body_lines.append(
                    f"{index}. {sku['sku_code']} - {sku['sku_name']} "
                    f"(score: {sku['score']})"
                )
                if sku.get("reason"):
                    body_lines.append(f"   Reason: {sku['reason']}")
        else:
            body_lines.append("No SKU recommendations are available for this cycle.")

        body_lines.extend([
            "",
            "Please reply with your confirmed monthly quantities for each SKU in this format:",
            "SKU11 - 100",
            "SKU12 - 200",
            "",
            "Regards,",
            "Demand Planning Team",
        ])
        return "\n".join(body_lines)
