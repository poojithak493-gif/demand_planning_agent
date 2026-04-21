"""
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
    """

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


def get_recommended_products(distributor_id: str, limit: int = 5):
    """
    Helper function for send_mail.py

    Returns only product names in a list format like:
    ["Product A", "Product B", "Product C"]
    """
    service = SKURecommendationService()
    result = service.execute(distributor_id=distributor_id, limit=limit)

    recommendations = result.get("recommendations", [])

    product_names = []

    for item in recommendations:
        if isinstance(item, dict):
            # Try common keys that may exist in graph response
            product_name = (
                item.get("sku_name")
                or item.get("product_name")
                or item.get("name")
                or str(item)
            )
            product_names.append(product_name)
        else:
            product_names.append(str(item))

    return product_names