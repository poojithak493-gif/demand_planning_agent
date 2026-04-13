from sqlalchemy.orm import Session
from app.models.primary_sales_model import PrimarySales


class PrimarySalesRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_sales(self):
        return self.db.query(PrimarySales).all()

    def get_sales_by_distributor(self, distributor_id: str):
        return (
            self.db.query(PrimarySales)
            .filter(PrimarySales.distributor_id == distributor_id)
            .all()
        )