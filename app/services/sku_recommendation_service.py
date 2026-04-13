from app.repositories.graph_repository import GraphRepository


class SKURecommendationService:
    def __init__(self):
        self.graph_repo = GraphRepository()

    def execute(self, distributor_id: str, limit: int = 5):
        recommendations = self.graph_repo.get_recommendations_for_distributor(
            distributor_id=distributor_id,
            limit=limit
        )

        return {
            "distributor_id": distributor_id,
            "recommendations": recommendations
        }