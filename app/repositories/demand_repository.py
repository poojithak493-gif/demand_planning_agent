from sqlalchemy import text

from app.core.database import SessionLocal


class DemandRepository:
    def get_active_cycle(self) -> dict | None:
        query = text("""
            SELECT
                cycle_id,
                cycle_date,
                cycle_label,
                status
            FROM demand_cycles
            WHERE status IN ('open', 'in_progress')
            ORDER BY
                CASE
                    WHEN status = 'in_progress' THEN 0
                    ELSE 1
                END,
                cycle_date DESC
            LIMIT 1
        """)

        with SessionLocal() as session:
            row = session.execute(query).mappings().first()
            return dict(row) if row else None

    def upsert_demand_record(
        self,
        distributor_id: str,
        sku_id: str,
        cycle_id: str,
        suggested_qty: float,
        confirmed_qty: float,
        confirmed_30d_qty: float,
        week1_qty: float,
        week2_qty: float,
        week3_qty: float,
        week4_qty: float,
        validation_status: str,
    ) -> str:
        query = text("""
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
                :validation_status
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

        with SessionLocal() as session:
            demand_id = session.execute(
                query,
                {
                    "distributor_id": distributor_id,
                    "sku_id": sku_id,
                    "cycle_id": cycle_id,
                    "suggested_qty": suggested_qty,
                    "confirmed_qty": confirmed_qty,
                    "confirmed_30d_qty": confirmed_30d_qty,
                    "week1_qty": week1_qty,
                    "week2_qty": week2_qty,
                    "week3_qty": week3_qty,
                    "week4_qty": week4_qty,
                    "validation_status": validation_status,
                },
            ).scalar_one()
            session.commit()

        return str(demand_id)

    def replace_validation_result(
        self,
        demand_id: str,
        overall_status: str,
        sku_valid: bool,
        distributor_valid: bool,
        qty_sanity_passed: bool,
        duplicate_check: bool,
        format_check: bool,
        failure_reason: str | None = None,
    ) -> None:
        delete_query = text("""
            DELETE FROM validation_results
            WHERE demand_id = :demand_id
        """)
        insert_query = text("""
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
                :sku_valid,
                :distributor_valid,
                :qty_sanity_passed,
                :duplicate_check,
                :format_check,
                :overall_status,
                :failure_reason
            )
        """)

        with SessionLocal() as session:
            session.execute(delete_query, {"demand_id": demand_id})
            session.execute(
                insert_query,
                {
                    "demand_id": demand_id,
                    "sku_valid": sku_valid,
                    "distributor_valid": distributor_valid,
                    "qty_sanity_passed": qty_sanity_passed,
                    "duplicate_check": duplicate_check,
                    "format_check": format_check,
                    "overall_status": overall_status,
                    "failure_reason": failure_reason,
                },
            )
            session.commit()
