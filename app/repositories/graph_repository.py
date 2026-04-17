from app.core.falkor_db import graph


class GraphRepository:
    @staticmethod
    def _escape(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("'", "\\'")

    def get_existing_skus_for_distributor(self, distributor_id: str) -> list[str]:
        distributor_id = self._escape(distributor_id)
        query = f"""
        MATCH (d:Distributor {{id: '{distributor_id}'}})-[:BOUGHT]->(s:SKU)
        RETURN s.id AS sku_id
        """

        result = graph.query(query)
        return [str(row[0]) for row in getattr(result, "result_set", []) if row]

    def get_recommendations_for_distributor(self, distributor_id: str, limit: int = 5):
        return self.get_related_recommendations(
            distributor_id=distributor_id,
            strong_sku_ids=[],
            preferred_categories=[],
            exclude_sku_ids=[],
            limit=limit,
        )

    def get_related_recommendations(
        self,
        distributor_id: str,
        strong_sku_ids: list[str],
        preferred_categories: list[str],
        exclude_sku_ids: list[str],
        limit: int = 8,
    ) -> list[dict]:
        distributor_id = self._escape(distributor_id)
        exclude_values = {
            self._escape(str(sku_id))
            for sku_id in exclude_sku_ids
            if sku_id
        }

        strong_candidates: list[dict] = []
        if strong_sku_ids:
            strong_list = ", ".join(
                f"'{self._escape(str(sku_id))}'"
                for sku_id in strong_sku_ids
                if sku_id
            )
            exclude_clause = ""
            if exclude_values:
                exclude_clause = "AND NOT rec.id IN [" + ", ".join(
                    f"'{sku_id}'" for sku_id in sorted(exclude_values)
                ) + "]"

            query = f"""
            MATCH (d:Distributor {{id: '{distributor_id}'}})
            MATCH (seed:SKU)
            WHERE seed.id IN [{strong_list}]
            MATCH (seed)-[rel:SIMILAR_TO|BOUGHT_WITH]->(rec:SKU)
            WHERE NOT (d)-[:BOUGHT]->(rec)
              {exclude_clause}
            RETURN rec.id AS sku_id,
                   rec.name AS sku_name,
                   rec.category AS category,
                   rec.brand_family AS brand_family,
                   COALESCE(rec.is_new_product, false) AS is_new_product,
                   SUM(
                       CASE
                           WHEN type(rel) = 'SIMILAR_TO' THEN 12
                           ELSE COALESCE(rel.weight, 1)
                       END
                   ) AS graph_score,
                   collect(DISTINCT seed.id) AS source_sku_ids
            ORDER BY graph_score DESC
            LIMIT {max(limit, 1)}
            """
            strong_candidates = self._run_candidate_query(query)

        category_candidates: list[dict] = []
        if preferred_categories:
            category_list = ", ".join(
                f"'{self._escape(category)}'"
                for category in preferred_categories
                if category
            )
            exclude_category_values = set(exclude_values)
            exclude_category_values.update(
                str(item["sku_id"])
                for item in strong_candidates
                if item.get("sku_id")
            )
            exclude_clause = ""
            if exclude_category_values:
                exclude_clause = "AND NOT rec.id IN [" + ", ".join(
                    f"'{self._escape(sku_id)}'" for sku_id in sorted(exclude_category_values)
                ) + "]"

            query = f"""
            MATCH (d:Distributor {{id: '{distributor_id}'}})
            MATCH (rec:SKU)-[:BELONGS_TO]->(c:Category)
            WHERE c.name IN [{category_list}]
              AND COALESCE(rec.is_new_product, false) = true
              AND NOT (d)-[:BOUGHT]->(rec)
              {exclude_clause}
            RETURN rec.id AS sku_id,
                   rec.name AS sku_name,
                   rec.category AS category,
                   rec.brand_family AS brand_family,
                   COALESCE(rec.is_new_product, false) AS is_new_product,
                   8 AS graph_score,
                   [] AS source_sku_ids
            ORDER BY graph_score DESC
            LIMIT {max(limit, 1)}
            """
            category_candidates = self._run_candidate_query(query)

        merged: dict[str, dict] = {}
        for candidate in strong_candidates + category_candidates:
            sku_id = candidate["sku_id"]
            existing = merged.get(sku_id)
            if existing is None or candidate["graph_score"] > existing["graph_score"]:
                merged[sku_id] = candidate
                continue

            existing_sources = set(existing.get("source_sku_ids", []))
            existing_sources.update(candidate.get("source_sku_ids", []))
            existing["source_sku_ids"] = sorted(existing_sources)

        return sorted(
            merged.values(),
            key=lambda item: (-item["graph_score"], item["sku_name"]),
        )[:limit]

    def _run_candidate_query(self, query: str) -> list[dict]:
        result = graph.query(query)
        recommendations = []
        for row in getattr(result, "result_set", []):
            recommendations.append({
                "sku_id": str(row[0]),
                "sku_name": row[1],
                "category": row[2],
                "brand_family": row[3],
                "is_new_product": bool(row[4]),
                "graph_score": row[5],
                "source_sku_ids": [str(item) for item in (row[6] or [])],
            })
        return recommendations
