from sqlalchemy import text
from app.core.database import SessionLocal


class SKURepository:
    def get_skus_for_distributor(self, distributor_code: str) -> list[dict]:
        query = text("""
            SELECT
                s.sku_id,
                s.sku_code,
                s.sku_name,
                s.category
            FROM skus s
            JOIN distributor_skus ds
              ON ds.sku_id = s.sku_id
            JOIN distributors d
              ON d.distributor_id = ds.distributor_id
            WHERE d.distributor_code = :distributor_code
              AND d.is_active = TRUE
              AND s.is_active = TRUE
              AND ds.is_active = TRUE
            ORDER BY s.sku_code
        """)

        with SessionLocal() as session:
            rows = session.execute(
                query,
                {"distributor_code": distributor_code}
            ).mappings().all()

            return [dict(row) for row in rows]

    def get_skus_by_ids(self, sku_ids: list[str]) -> dict[str, dict]:
        normalized_ids = [str(sku_id) for sku_id in sku_ids if sku_id is not None]
        if not normalized_ids:
            return {}

        query = text("""
            SELECT
                sku_id,
                sku_code,
                sku_name,
                category
            FROM skus
            WHERE CAST(sku_id AS TEXT) = ANY(:sku_ids)
              AND is_active = TRUE
        """)

        with SessionLocal() as session:
            rows = session.execute(
                query,
                {"sku_ids": normalized_ids}
            ).mappings().all()

        return {
            str(row["sku_id"]): dict(row)
            for row in rows
        }
