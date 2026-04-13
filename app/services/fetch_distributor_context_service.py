from app.repositories.primary_sales_repository import PrimarySalesRepository
from app.repositories.graph_repository import GraphRepository


class FetchDistributorContextService:
    def __init__(self, db):
        self.sales_repo = PrimarySalesRepository(db)
        self.graph_repo = GraphRepository()

    def execute(self, distributor_id: str):
        sales_rows = self.sales_repo.get_sales_by_distributor(distributor_id)
        existing_skus = self.graph_repo.get_existing_skus_for_distributor(distributor_id)

        return {
            "distributor_id": distributor_id,
            "historical_rows_count": len(sales_rows),
            "existing_skus": existing_skus
        }