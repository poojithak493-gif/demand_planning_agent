from app.repositories.sku_repository import SKURepository
from app.services.distributor_service import DistributorService


class RecommendationService:
    def __init__(self) -> None:
        self.distributor_service = DistributorService()
        self.sku_repository = SKURepository()

    def get_sku_recommendations(self, distributor_code: str) -> dict:
        distributor = self.distributor_service.get_distributor_context(distributor_code)
        skus = self.sku_repository.get_skus_for_distributor(distributor_code)

        recommendations = []
        base_bonus = 20 if distributor["priority"] == "High" else 10

        for index, sku in enumerate(skus, start=1):
            score = max(100 - index, 1) + base_bonus
            recommendations.append({
                "sku_id": str(sku["sku_id"]),
                "sku_code": sku["sku_code"],
                "sku_name": sku["sku_name"],
                "category": sku["category"],
                "score": score,
                "reason": f"Mapped to distributor {distributor_code} and prioritized for {distributor['priority']} tier"
            })

        return {
            "distributor_code": distributor["distributor_code"],
            "distributor_name": distributor["name"],
            "recommended_skus": recommendations[:5]
        }