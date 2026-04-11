from typing import List

from app.repositories.sku_repository import SKURepository
from app.services.distributor_service import DistributorService
from app.services.validation_service import ValidationService


class RecommendationService:
    def __init__(self) -> None:
        self.distributor_service = DistributorService()
        self.sku_repository = SKURepository()

    def get_sku_recommendations(self, distributor_id: str) -> dict:
        distributor = self.distributor_service.get_distributor_context(distributor_id)
        all_skus = self.sku_repository.get_all()

        recommendations: List[dict] = []

        for sku in all_skus:
            ValidationService.validate_sku_data(sku)

            score = 0
            reasons = []

            if distributor["region"] in sku["regions"]:
                score += 40
                reasons.append(f"Matches region {distributor['region']}")

            if distributor["channel"] in sku["channels"]:
                score += 30
                reasons.append(f"Matches channel {distributor['channel']}")

            score += sku["base_score"] // 5

            if distributor["priority"].lower() == "high":
                score += 10
                reasons.append("High priority distributor")

            if distributor["recent_order_volume"] >= 1000:
                score += 10
                reasons.append("Strong recent order volume")

            if score > 0:
                recommendations.append(
                    {
                        "sku_id": sku["sku_id"],
                        "sku_name": sku["sku_name"],
                        "score": score,
                        "reason": ", ".join(reasons),
                    }
                )

        recommendations.sort(key=lambda item: item["score"], reverse=True)

        return {
            "distributor_id": distributor["distributor_id"],
            "distributor_name": distributor["name"],
            "recommended_skus": recommendations[:3],
        }