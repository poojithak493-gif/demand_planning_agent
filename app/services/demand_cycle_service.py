from app.services.demand_persistence_service import DemandPersistenceService
from app.services.demand_plan_service import DemandPlanService
from app.services.demand_planning_service import DemandPlanningService
from app.services.email_payload_service import EmailPayloadService
from app.services.reply_parse_service import ReplyParseService
from app.services.validation_service import ValidationService


class DemandCycleService:
    def __init__(self) -> None:
        self.demand_plan_service = DemandPlanService()
        self.email_payload_service = EmailPayloadService()
        self.demand_persistence_service = DemandPersistenceService()
        self.reply_parse_service = ReplyParseService()
        self.validation_service = ValidationService()
        self.demand_planning_service = DemandPlanningService()

    def run_mocked_demand_cycle(self, distributor_code: str) -> dict:
        demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
        email_payload = self.email_payload_service.build_email_payload(distributor_code)
        parsed_reply = self.reply_parse_service.parse_reply(
            distributor_code=distributor_code,
            confirmed_by="Mock Distributor Contact",
        ).model_dump()
        return self._build_combined_response(
            distributor_code=distributor_code,
            demand_plan=demand_plan,
            email_payload=email_payload,
            parsed_reply=parsed_reply,
            persist_result=False,
        )

    def process_reply_cycle(self, distributor_code: str, reply_payload: dict) -> dict:
        demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
        email_payload = self.email_payload_service.build_email_payload(distributor_code)
        parsed_reply = self.demand_plan_service.build_parsed_reply(
            distributor_code,
            reply_payload,
        )

        return self._build_combined_response(
            distributor_code=distributor_code,
            demand_plan=demand_plan,
            email_payload=email_payload,
            parsed_reply=parsed_reply,
            persist_result=True,
        )

    def process_reply(self, distributor_code: str, email_body: str) -> dict:
        demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
        parsed_reply = self.reply_parse_service.parse_reply(
            distributor_code=distributor_code,
            raw_reply_text=email_body,
        ).model_dump()
        validation_result = self.validation_service.validate_parsed_reply(
            parsed_reply,
            recommended_skus=demand_plan["recommended_skus"],
        )
        weekly_demand_plan = self.demand_planning_service.build_weekly_plan(
            distributor_code=distributor_code,
            parsed_lines=parsed_reply["parsed_lines"],
        )
        saved_status = {"saved": False, "inserted_rows": 0, "cycle_id": None}

        if validation_result["is_valid"]:
            saved_status = self.demand_persistence_service.save(
                distributor_code=distributor_code,
                parsed_lines=parsed_reply["parsed_lines"],
                weekly_plan=weekly_demand_plan,
                recommended_skus=demand_plan["recommended_skus"],
            )

        return {
            "parsed_reply": parsed_reply,
            "validation_result": validation_result,
            "weekly_demand_plan": weekly_demand_plan,
            "saved_status": saved_status,
        }

    def _build_combined_response(
        self,
        distributor_code: str,
        demand_plan: dict,
        email_payload: dict,
        parsed_reply: dict,
        persist_result: bool,
    ) -> dict:
        validation_result = self.validation_service.validate_parsed_reply(
            parsed_reply,
            recommended_skus=demand_plan["recommended_skus"],
        )
        weekly_demand_plan = self.demand_planning_service.build_weekly_plan(
            distributor_code=distributor_code,
            parsed_lines=parsed_reply["parsed_lines"],
        )
        if persist_result and validation_result["is_valid"]:
            self.demand_persistence_service.save(
                distributor_code=distributor_code,
                parsed_lines=parsed_reply["parsed_lines"],
                weekly_plan=weekly_demand_plan,
                recommended_skus=demand_plan["recommended_skus"],
            )

        return {
            "distributor_code": distributor_code,
            "demand_plan": demand_plan,
            "email_payload": email_payload,
            "parsed_reply": parsed_reply,
            "validation_result": validation_result,
            "weekly_demand_plan": weekly_demand_plan,
        }
