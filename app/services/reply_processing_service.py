from app.services.demand_persistence_service import DemandPersistenceService
from app.services.demand_plan_service import DemandPlanService
from app.services.demand_planning_service import DemandPlanningService
from app.services.distributor_service import DistributorService
from app.services.helpers.process_replies import ingest_replies
from app.services.reply_parse_service import ReplyParseService
from app.services.validation_service import ValidationService


class ReplyProcessingService:
    def __init__(self) -> None:
        self.distributor_service = DistributorService()
        self.demand_plan_service = DemandPlanService()
        self.reply_parse_service = ReplyParseService()
        self.validation_service = ValidationService()
        self.demand_planning_service = DemandPlanningService()
        self.demand_persistence_service = DemandPersistenceService()

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
        mail_response_status = self.demand_persistence_service.record_inbound_mail_response(
            distributor_code=distributor_code,
            from_email=from_email,
            subject=subject,
            raw_body=email_body,
            received_at=received_at,
            processing_status="received",
            parse_status="pending",
            notes=notes,
        )

        try:
            demand_plan = self.demand_plan_service.get_demand_plan(distributor_code)
            parsed_reply = self.reply_parse_service.parse_reply(
                distributor_code=distributor_code,
                raw_reply_text=email_body,
                confirmed_by=confirmed_by or from_email,
                notes=notes,
            ).model_dump()
            mail_response_status = self.demand_persistence_service.update_inbound_mail_response(
                mail_response_id=mail_response_status["mail_response_id"],
                processing_status="parsed",
                parse_status="parsed",
                notes=parsed_reply.get("notes"),
            )
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
                mail_response_status = self.demand_persistence_service.update_inbound_mail_response(
                    mail_response_id=mail_response_status["mail_response_id"],
                    processing_status="persisted",
                    parse_status="parsed",
                    notes=parsed_reply.get("notes"),
                )
            else:
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
        except Exception as exc:
            self.demand_persistence_service.update_inbound_mail_response(
                mail_response_id=mail_response_status["mail_response_id"],
                processing_status="failed",
                parse_status="failed",
                notes=str(exc),
            )
            raise

    def process_inbox(
        self,
        simulated_messages: list[dict] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        normalized_messages = ingest_replies(
            simulated_messages=simulated_messages,
            limit=limit,
        )
        results: list[dict] = []

        for message in normalized_messages:
            distributor_code = message.get("distributor_code")
            if not distributor_code and message.get("from_email"):
                try:
                    distributor = self.distributor_service.get_distributor_by_email(
                        message["from_email"]
                    )
                    distributor_code = distributor["distributor_code"]
                except ValueError:
                    distributor_code = None

            if not distributor_code:
                mail_response_status = self.demand_persistence_service.record_inbound_mail_response(
                    distributor_code=None,
                    from_email=message.get("from_email"),
                    subject=message.get("subject"),
                    raw_body=message.get("raw_body") or "",
                    received_at=message.get("received_at"),
                    processing_status="failed",
                    parse_status="failed",
                    notes="Unable to resolve distributor_code for inbound reply",
                )
                results.append(
                    {
                        "message_id": message.get("message_id"),
                        "mail_response_status": mail_response_status,
                        "error": "Unable to resolve distributor_code for inbound reply",
                    }
                )
                continue

            results.append(
                self.process_reply(
                    distributor_code=distributor_code,
                    email_body=message.get("raw_body") or "",
                    from_email=message.get("from_email"),
                    subject=message.get("subject"),
                    confirmed_by=message.get("confirmed_by") or message.get("from_email"),
                    notes=message.get("notes"),
                    received_at=message.get("received_at"),
                )
            )

        return results
