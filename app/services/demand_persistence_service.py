from datetime import datetime, timezone

from sqlalchemy import text

from app.core.database import SessionLocal
from app.repositories.demand_repository import DemandRepository
from app.repositories.distributor_repository import DistributorRepository
from app.repositories.sku_repository import SKURepository


class DemandPersistenceService:
    def __init__(self) -> None:
        self.demand_repository = DemandRepository()
        self.distributor_repository = DistributorRepository()
        self.sku_repository = SKURepository()

    def save(
        self,
        distributor_code: str,
        parsed_lines: list[dict],
        weekly_plan: dict,
        recommended_skus: list[dict],
    ) -> dict:
        distributor = self.distributor_repository.get_by_code(distributor_code)
        if not distributor:
            raise ValueError(f"Distributor '{distributor_code}' not found")

        cycle = self._get_latest_cycle()
        if not cycle:
            raise ValueError("No demand cycle found for persistence")

        sku_lookup = self.sku_repository.get_skus_by_codes(
            [line.get("sku_code") for line in parsed_lines if line.get("sku_code")]
        )
        weekly_plan_lookup = {
            str(item.get("sku_code") or "").strip().upper(): item
            for item in weekly_plan.get("weekly_plan", [])
            if item.get("sku_code")
        }
        recommendation_lookup = {
            str(item.get("sku_code") or "").strip().upper(): item
            for item in recommended_skus
            if item.get("sku_code")
        }

        upsert_query = text("""
            INSERT INTO demand_records (
                distributor_id,
                sku_id,
                cycle_id,
                suggested_qty,
                confirmed_qty,
                confirmed_30d_qty,
                week1_qty,
                week2_qty,
                week3_qty,
                week4_qty,
                reply_received_at,
                validation_status
            )
            VALUES (
                :distributor_id,
                :sku_id,
                :cycle_id,
                :suggested_qty,
                :confirmed_qty,
                :confirmed_30d_qty,
                :week1_qty,
                :week2_qty,
                :week3_qty,
                :week4_qty,
                NOW(),
                'passed'
            )
            ON CONFLICT (distributor_id, sku_id, cycle_id)
            DO UPDATE SET
                suggested_qty = EXCLUDED.suggested_qty,
                confirmed_qty = EXCLUDED.confirmed_qty,
                confirmed_30d_qty = EXCLUDED.confirmed_30d_qty,
                week1_qty = EXCLUDED.week1_qty,
                week2_qty = EXCLUDED.week2_qty,
                week3_qty = EXCLUDED.week3_qty,
                week4_qty = EXCLUDED.week4_qty,
                reply_received_at = EXCLUDED.reply_received_at,
                validation_status = EXCLUDED.validation_status,
                updated_at = NOW()
            RETURNING demand_id
        """)
        replace_validation_query = text("""
            DELETE FROM validation_results
            WHERE demand_id = :demand_id
        """)
        insert_validation_query = text("""
            INSERT INTO validation_results (
                demand_id,
                sku_valid,
                distributor_valid,
                qty_sanity_passed,
                duplicate_check,
                format_check,
                overall_status,
                failure_reason
            )
            VALUES (
                :demand_id,
                TRUE,
                TRUE,
                TRUE,
                TRUE,
                TRUE,
                'passed',
                NULL
            )
        """)

        inserted_rows = 0
        with SessionLocal() as session:
            try:
                for line in parsed_lines:
                    sku_code = str(line.get("sku_code") or "").strip().upper()
                    monthly_quantity = line.get("monthly_quantity")
                    weekly_line = weekly_plan_lookup.get(sku_code)
                    sku_record = sku_lookup.get(sku_code)

                    if (
                        not sku_code
                        or monthly_quantity is None
                        or monthly_quantity <= 0
                        or weekly_line is None
                        or sku_record is None
                    ):
                        continue

                    recommendation = recommendation_lookup.get(sku_code, {})
                    suggested_qty = float(recommendation.get("score") or 0)
                    demand_id = session.execute(
                        upsert_query,
                        {
                            "distributor_id": str(distributor["distributor_id"]),
                            "sku_id": str(sku_record["sku_id"]),
                            "cycle_id": str(cycle["cycle_id"]),
                            "suggested_qty": suggested_qty,
                            "confirmed_qty": float(monthly_quantity),
                            "confirmed_30d_qty": float(monthly_quantity),
                            "week1_qty": float(weekly_line["week1_qty"]),
                            "week2_qty": float(weekly_line["week2_qty"]),
                            "week3_qty": float(weekly_line["week3_qty"]),
                            "week4_qty": float(weekly_line["week4_qty"]),
                        },
                    ).scalar_one()
                    session.execute(
                        replace_validation_query,
                        {"demand_id": str(demand_id)},
                    )
                    session.execute(
                        insert_validation_query,
                        {"demand_id": str(demand_id)},
                    )
                    inserted_rows += 1

                session.commit()
            except Exception:
                session.rollback()
                raise

        return {
            "saved": True,
            "inserted_rows": inserted_rows,
            "cycle_id": str(cycle["cycle_id"]),
        }

    def record_inbound_mail_response(
        self,
        distributor_code: str | None,
        from_email: str | None,
        subject: str | None,
        raw_body: str,
        received_at: str | None = None,
        processing_status: str = "received",
        parse_status: str = "pending",
        notes: str | None = None,
    ) -> dict:
        distributor = (
            self.distributor_repository.get_by_code(distributor_code)
            if distributor_code
            else None
        )
        received_timestamp = received_at or datetime.now(timezone.utc).isoformat()
        insert_query = text("""
            INSERT INTO inbound_mail_responses (
                distributor_id,
                distributor_code,
                from_email,
                subject,
                raw_body,
                received_at,
                processing_status,
                parse_status,
                notes
            )
            VALUES (
                :distributor_id,
                :distributor_code,
                :from_email,
                :subject,
                :raw_body,
                :received_at,
                :processing_status,
                :parse_status,
                :notes
            )
            RETURNING id
        """)

        with SessionLocal() as session:
            response_id = session.execute(
                insert_query,
                {
                    "distributor_id": str(distributor["distributor_id"]) if distributor else None,
                    "distributor_code": distributor_code,
                    "from_email": from_email,
                    "subject": subject,
                    "raw_body": raw_body,
                    "received_at": received_timestamp,
                    "processing_status": processing_status,
                    "parse_status": parse_status,
                    "notes": notes,
                },
            ).scalar_one()
            session.commit()

        return {
            "mail_response_id": int(response_id),
            "processing_status": processing_status,
            "parse_status": parse_status,
        }

    def update_inbound_mail_response(
        self,
        mail_response_id: int,
        processing_status: str,
        parse_status: str,
        notes: str | None = None,
    ) -> dict:
        update_query = text("""
            UPDATE inbound_mail_responses
            SET
                processing_status = :processing_status,
                parse_status = :parse_status,
                notes = :notes,
                updated_at = NOW()
            WHERE id = :response_id
        """)

        with SessionLocal() as session:
            session.execute(
                update_query,
                {
                    "response_id": mail_response_id,
                    "processing_status": processing_status,
                    "parse_status": parse_status,
                    "notes": notes,
                },
            )
            session.commit()

        return {
            "mail_response_id": mail_response_id,
            "processing_status": processing_status,
            "parse_status": parse_status,
        }

    def _get_latest_cycle(self) -> dict | None:
        cycle = self.demand_repository.get_active_cycle()
        if cycle:
            return cycle

        query = text("""
            SELECT
                cycle_id,
                cycle_date,
                cycle_label,
                status
            FROM demand_cycles
            ORDER BY cycle_date DESC
            LIMIT 1
        """)
        with SessionLocal() as session:
            row = session.execute(query).mappings().first()
            return dict(row) if row else None
