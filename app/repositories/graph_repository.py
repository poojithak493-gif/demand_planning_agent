from app.core.falkor_db import graph


class GraphRepository:
    def get_recommendations_for_distributor(self, distributor_id: str, limit: int = 5):
        distributor_id = str(distributor_id).replace("\\", "\\\\").replace("'", "\\'")
        query = f"""
        MATCH (d:Distributor {{id: '{distributor_id}'}})-[:BOUGHT]->(s:SKU)
        MATCH (s)-[bw:BOUGHT_WITH]->(rec:SKU)
        WHERE NOT (d)-[:BOUGHT]->(rec)
        RETURN rec.id AS sku_id, rec.name AS sku_name, SUM(bw.weight) AS score
        ORDER BY score DESC
        LIMIT {limit}
        """
        result = graph.query(query)

        recommendations = []
        for row in result.result_set:
            recommendations.append({
                "sku_id": row[0],
                "sku_name": row[1],
                "score": float(row[2]) if row[2] is not None else 0.0
            })
        return recommendations

    def get_existing_skus_for_distributor(self, distributor_id: str):
        distributor_id = str(distributor_id).replace("\\", "\\\\").replace("'", "\\'")
        query = f"""
        MATCH (d:Distributor {{id: '{distributor_id}'}})-[:BOUGHT]->(s:SKU)
        RETURN s.id AS sku_id, s.name AS sku_name
        """
        result = graph.query(query)

        skus = []
        for row in result.result_set:
            skus.append({
                "sku_id": row[0],
                "sku_name": row[1]
            })
        return skus