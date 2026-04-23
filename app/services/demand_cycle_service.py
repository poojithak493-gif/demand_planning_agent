from app.services.demand_persistence_service import DemandPersistenceService
from app.services.demand_plan_service import DemandPlanService
from app.services.demand_planning_service import DemandPlanningService
from app.services.email_payload_service import EmailPayloadService
from app.services.reply_processing_service import ReplyProcessingService
from app.services.validation_service import ValidationService


class DemandCycleService:
    def __init__(self) -> None:
        self.demand_plan_service = DemandPlanService()
        self.email_payload_service = EmailPayloadService()
        self.demand_persistence_service = DemandPersistenceService()
        self.reply_processing_service = ReplyProcessingService()
        self.validation_service = ValidationService()
        self.demand_planning_service = DemandPlanningService()

    def process_reply_cycle(self, distributor_code: str, reply_payload: dict) -> dict:
        demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
        email_payload = self.email_payload_service.build_email_payload(distributor_code)
        if reply_payload.get("raw_reply_text"):
            reply_result = self.reply_processing_service.process_reply(
                distributor_code=distributor_code,
                email_body=reply_payload["raw_reply_text"],
                from_email=reply_payload.get("from_email"),
                subject=reply_payload.get("subject"),
                confirmed_by=reply_payload.get("confirmed_by"),
                notes=reply_payload.get("notes"),
                received_at=reply_payload.get("received_at"),
            )
        else:
            parsed_reply = self.demand_plan_service.build_parsed_reply(
                distributor_code,
                reply_payload,
            )
            reply_result = self._build_reply_result(
                distributor_code=distributor_code,
                parsed_reply=parsed_reply,
                recommended_skus=demand_plan["recommended_skus"],
                persist_result=True,
                from_email=reply_payload.get("from_email"),
                subject=reply_payload.get("subject"),
                raw_body=reply_payload.get("notes") or "",
                received_at=reply_payload.get("received_at"),
                notes=reply_payload.get("notes"),
            )

        return {
            "distributor_code": distributor_code,
            "demand_plan": demand_plan,
            "email_payload": email_payload,
            "parsed_reply": reply_result["parsed_reply"],
            "validation_result": reply_result["validation_result"],
            "weekly_demand_plan": reply_result["weekly_demand_plan"],
        }

    def process_reply(
        self,
        distributor_code: str,
        email_body: str,
        from_email: str | None = None,
        subject: str | None = None,
        confirmed_by: str | None = None,
        notes: str | None = None,
        received_at: str | None = None,
    ) -> dict:
        return self.reply_processing_service.process_reply(
            distributor_code=distributor_code,
            email_body=email_body,
            from_email=from_email,
            subject=subject,
            confirmed_by=confirmed_by,
            notes=notes,
            received_at=received_at,
        )

    def send_demand_email(
        self,
        distributor_code: str,
        attachment_path: str | None = None,
    ) -> dict:
        return self.email_payload_service.send_email_payload(
            distributor_code=distributor_code,
            attachment_path=attachment_path,
        )

    def _build_reply_result(
        self,
        distributor_code: str,
        parsed_reply: dict,
        recommended_skus: list[dict],
        persist_result: bool,
        from_email: str | None = None,
        subject: str | None = None,
        raw_body: str | None = None,
        received_at: str | None = None,
        notes: str | None = None,
    ) -> dict:
        mail_response_status = self.demand_persistence_service.record_inbound_mail_response(
            distributor_code=distributor_code,
            from_email=from_email,
            subject=subject,
            raw_body=raw_body or "",
            received_at=received_at,
            processing_status="parsed",
            parse_status="parsed",
            notes=notes,
        )
        validation_result = self.validation_service.validate_parsed_reply(
            parsed_reply,
            recommended_skus=recommended_skus,
        )
        weekly_demand_plan = self.demand_planning_service.build_weekly_plan(
            distributor_code=distributor_code,
            parsed_lines=parsed_reply["parsed_lines"],
        )
        saved_status = {"saved": False, "inserted_rows": 0, "cycle_id": None}
        if persist_result and validation_result["is_valid"]:
            saved_status = self.demand_persistence_service.save(
                distributor_code=distributor_code,
                parsed_lines=parsed_reply["parsed_lines"],
                weekly_plan=weekly_demand_plan,
                recommended_skus=recommended_skus,
            )
            mail_response_status = self.demand_persistence_service.update_inbound_mail_response(
                mail_response_id=mail_response_status["mail_response_id"],
                processing_status="persisted",
                parse_status="parsed",
                notes=notes,
            )
        elif persist_result:
            mail_response_status = self.demand_persistence_service.update_inbound_mail_response(
                mail_response_id=mail_response_status["mail_response_id"],
                processing_status="validation_failed",
                parse_status="parsed",
                notes="; ".join(issue["message"] for issue in validation_result["issues"]) or notes,
            )

        return {
            "parsed_reply": parsed_reply,
            "validation_result": validation_result,
            "weekly_demand_plan": weekly_demand_plan,
            "saved_status": saved_status,
            "mail_response_status": mail_response_status,
        }
