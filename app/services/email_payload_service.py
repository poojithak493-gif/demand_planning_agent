from app.services.demand_plan_service import DemandPlanService


class EmailPayloadService:
    def __init__(self) -> None:
        self.demand_plan_service = DemandPlanService()

    def build_email_payload(self, distributor_code: str) -> dict:
        demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
        distributor = demand_plan["distributor"]
        recommended_skus = demand_plan["recommended_skus"]

        body_lines = [
            f"Hello {distributor['name']},",
            "",
            "Please review the recommended SKUs below for the upcoming demand plan.",
            "",
        ]

        for sku in recommended_skus:
            body_lines.append(
                f"- {sku['sku_code']} ({sku['sku_name']}): score {sku['score']}"
            )

        body_lines.extend([
            "",
            "Please reply with your confirmed monthly quantities for each SKU.",
        ])

        return {
            "distributor_code": distributor["distributor_code"],
            "distributor_name": distributor["name"],
            "email_subject": (
                f"Demand Plan Recommendation for {distributor['distributor_code']}"
            ),
            "email_body": "\n".join(body_lines),
            "recommended_skus": recommended_skus,
        }
