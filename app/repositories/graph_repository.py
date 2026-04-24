from app.core.falkor_db import graph


class GraphRepository:
    def get_recommendations_for_distributor(self, distributor_id: str, limit: int = 5):
        distributor_id = self._sanitize(distributor_id)
        limit = int(limit)

        # ---------------------------------------------------------
        # Primary logic:
        # 1. Find SKUs already bought by target distributor
        # 2. Find other distributors who bought same SKUs
        # 3. Find additional SKUs bought by those distributors
        # 4. Exclude SKUs already bought by target distributor
        # 5. Rank by frequency
        # ---------------------------------------------------------
        collaborative_query = f"""
        MATCH (d:Distributor {{id: '{distributor_id}'}})-[:BOUGHT]->(owned:SKU)
        MATCH (other:Distributor)-[:BOUGHT]->(owned)
        WHERE other.id <> '{distributor_id}'
        MATCH (other)-[:BOUGHT]->(rec:SKU)
        WHERE NOT (d)-[:BOUGHT]->(rec)
        RETURN
            rec.id AS sku_id,
            rec.name AS sku_name,
            rec.brand_family AS brand_family,
            rec.category AS category,
            COUNT(DISTINCT other) AS score
        ORDER BY score DESC, sku_name ASC
        LIMIT {limit}
        """

        result = graph.query(collaborative_query)
        recommendations = self._format_results(result)

        if recommendations:
            return recommendations

        # ---------------------------------------------------------
        # Fallback logic:
        # Use SKU-to-SKU relationships if collaborative results are empty
        # ---------------------------------------------------------
        fallback_query = f"""
        MATCH (d:Distributor {{id: '{distributor_id}'}})-[:BOUGHT]->(oldsku:SKU)
        MATCH (oldsku)-[:SIMILAR_TO|BOUGHT_WITH]->(rec:SKU)
        WHERE NOT (d)-[:BOUGHT]->(rec)
        RETURN
            rec.id AS sku_id,
            rec.name AS sku_name,
            rec.brand_family AS brand_family,
            rec.category AS category,
            COUNT(rec) AS score
        ORDER BY score DESC, sku_name ASC
        LIMIT {limit}
        """

        fallback_result = graph.query(fallback_query)
        return self._format_results(fallback_result)

    def _format_results(self, result):
        recommendations = []

        if not result or not hasattr(result, "result_set"):
            return recommendations

        for row in result.result_set:
            recommendations.append({
                "sku_id": row[0],
                "sku_name": row[1],
                "brand_family": row[2],
                "category": row[3],
                "score": row[4]
            })

        return recommendations

    def _sanitize(self, value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("'", "\\'")