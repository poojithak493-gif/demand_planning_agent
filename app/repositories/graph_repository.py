from app.core.falkor_db import graph


class GraphRepository:
    def get_recommendations_for_distributor(self, distributor_id: str, limit: int = 5):
        distributor_id = str(distributor_id).replace("\\", "\\\\").replace("'", "\\'")

        query = f"""
        MATCH (d:Distributor {{id: '{distributor_id}'}})-[:BOUGHT]->(oldsku:SKU)
        MATCH (oldsku)-[:SIMILAR_TO|BOUGHT_WITH]->(rec:SKU)
        WHERE rec.is_new_product = true
          AND NOT (d)-[:BOUGHT]->(rec)
        RETURN rec.id AS sku_id,
               rec.name AS sku_name,
               rec.brand_family AS brand_family,
               rec.category AS category,
               COUNT(rec) AS score
        ORDER BY score DESC
        LIMIT {limit}
        """

        result = graph.query(query)

        recommendations = []
        for row in result.result_set:
            recommendations.append({
                "sku_id": row[0],
                "sku_name": row[1],
                "brand_family": row[2],
                "category": row[3],
                "score": row[4]
            })

        return recommendations