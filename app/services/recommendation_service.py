from app.repositories.sku_repository import SKURepository
from app.services.distributor_service import DistributorService
from app.services.helpers.sku_recommendation_service import SKURecommendationService


class RecommendationService:
    def __init__(self) -> None:
        self.distributor_service = DistributorService()
        self.sku_repository = SKURepository()
        self.graph_recommendation_service = SKURecommendationService()

    def get_sku_recommendations(self, distributor_code: str) -> dict:
        distributor = self.distributor_service.get_distributor_context(distributor_code)
        skus = self.sku_repository.get_skus_for_distributor(distributor_code)

        recommendations_by_code: dict[str, dict] = {}
        base_bonus = 20 if distributor["priority"] == "High" else 10

        for index, sku in enumerate(skus, start=1):
            score = max(100 - index, 1) + base_bonus
            recommendation = {
                "sku_id": str(sku["sku_id"]),
                "sku_code": sku["sku_code"],
                "sku_name": sku["sku_name"],
                "category": sku["category"],
                "score": score,
                "reason": (
                    f"Mapped to distributor {distributor_code} and prioritized "
                    f"for {distributor['priority']} tier"
                ),
            }
            recommendations_by_code[recommendation["sku_code"]] = recommendation

        for recommendation in self._get_graph_recommendations(distributor):
            sku_code = recommendation["sku_code"]
            if sku_code in recommendations_by_code:
                merged = recommendations_by_code[sku_code]
                merged["score"] = max(merged["score"], recommendation["score"])
                if recommendation["reason"] not in merged["reason"]:
                    merged["reason"] = f"{merged['reason']}; {recommendation['reason']}"
                if not merged.get("category"):
                    merged["category"] = recommendation.get("category")
                continue

            recommendations_by_code[sku_code] = recommendation

        recommendations = sorted(
            recommendations_by_code.values(),
            key=lambda item: (-item["score"], item["sku_code"]),
        )

        return {
            "distributor_code": distributor["distributor_code"],
            "distributor_name": distributor["name"],
            "recommended_skus": recommendations[:5]
        }

    def _get_graph_recommendations(self, distributor: dict) -> list[dict]:
        distributor_id = str(distributor["distributor_id"])
        try:
            helper_response = self.graph_recommendation_service.execute(distributor_id)
        except Exception:
            return []

        raw_recommendations = helper_response.get("recommendations", [])
        if not raw_recommendations:
            return []

        normalized_recommendations = []
        for item in raw_recommendations:
            normalized = self._normalize_graph_recommendation(item)
            if normalized:
                normalized_recommendations.append(normalized)

        return normalized_recommendations

    @staticmethod
    def _normalize_graph_recommendation(recommendation: dict) -> dict | None:
        sku_id = recommendation.get("sku_id")
        if sku_id is None:
            return None

        sku_id_str = str(sku_id)
        sku_code = recommendation.get("sku_code") or sku_id_str
        sku_name = recommendation.get("sku_name") or sku_code
        category = recommendation.get("category")
        raw_score = recommendation.get("score", 0)

        try:
            score = int(raw_score)
        except (TypeError, ValueError):
            score = 0

        return {
            "sku_id": sku_id_str,
            "sku_code": sku_code,
            "sku_name": sku_name,
            "category": category,
            "score": score,
            "reason": "Graph recommendation enhancement from FalkorDB",
        }
