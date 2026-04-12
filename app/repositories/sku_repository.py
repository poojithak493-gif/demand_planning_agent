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