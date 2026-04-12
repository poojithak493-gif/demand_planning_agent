from sqlalchemy import text
from app.core.database import SessionLocal


class DistributorRepository:
    def get_by_code(self, distributor_code: str) -> dict | None:
        query = text("""
            SELECT
                distributor_id,
                distributor_code,
                name,
                email,
                phone,
                region,
                priority,
                is_active
            FROM distributors
            WHERE distributor_code = :distributor_code
              AND is_active = TRUE
            LIMIT 1
        """)

        with SessionLocal() as session:
            row = session.execute(
                query,
                {"distributor_code": distributor_code}
            ).mappings().first()

            return dict(row) if row else None