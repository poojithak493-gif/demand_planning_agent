from app.services.distributor_service import DistributorService
from app.services.demand_planning_service import DemandPlanningService
from app.services.recommendation_service import RecommendationService
from app.services.reply_parse_service import ReplyParseService
from app.services.validation_service import ValidationService


class DemandPlanService:
    def __init__(self) -> None:
        self.distributor_service = DistributorService()
        self.demand_planning_service = DemandPlanningService()
        self.recommendation_service = RecommendationService()
        self.reply_parse_service = ReplyParseService()
        self.validation_service = ValidationService()

    def get_demand_plan(self, distributor_code: str) -> dict:
        distributor = self.distributor_service.get_distributor_context(distributor_code)
        recommendations = self.recommendation_service.get_sku_recommendations(distributor_code)

        return {
            "distributor": distributor,
            "recommended_skus": recommendations["recommended_skus"],
        }

    def process_reply(self, distributor_code: str, reply_payload: dict) -> dict:
        distributor = self.distributor_service.get_distributor_context(distributor_code)
        recommendations = self.recommendation_service.get_sku_recommendations(distributor_code)
        parsed_reply = self.build_parsed_reply(distributor_code, reply_payload)
        validation_result = self.validation_service.validate_parsed_reply(
            parsed_reply,
            recommended_skus=recommendations["recommended_skus"],
        )
        weekly_plan_response = self.demand_planning_service.build_weekly_plan(
            distributor_code=distributor_code,
            parsed_lines=parsed_reply["parsed_lines"],
        )

        return {
            "distributor_code": distributor["distributor_code"],
            "distributor_name": distributor["name"],
            "confirmed_by": parsed_reply.get("confirmed_by") or reply_payload["confirmed_by"],
            "notes": parsed_reply.get("notes"),
            "is_valid": validation_result["is_valid"],
            "issues": validation_result["issues"],
            "weekly_plan": weekly_plan_response["weekly_plan"],
        }

    def build_parsed_reply(self, distributor_code: str, reply_payload: dict) -> dict:
        raw_reply_text = reply_payload.get("raw_reply_text")
        if raw_reply_text:
            return self.reply_parse_service.parse_reply(
                distributor_code=distributor_code,
                raw_reply_text=raw_reply_text,
                confirmed_by=reply_payload.get("confirmed_by"),
                notes=reply_payload.get("notes"),
            ).model_dump()

        return {
            "distributor_code": distributor_code,
            "confirmed_by": reply_payload.get("confirmed_by"),
            "notes": reply_payload.get("notes"),
            "parsed_lines": [
                {
                    "sku_code": str(item.get("sku_code") or "").strip().upper(),
                    "sku_name": None,
                    "monthly_quantity": item.get("monthly_quantity"),
                    "raw_text": None,
                }
                for item in reply_payload.get("items", [])
            ],
        }
