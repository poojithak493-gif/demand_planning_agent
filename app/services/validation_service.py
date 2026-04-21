from app.repositories.sku_repository import SKURepository
from app.services.recommendation_service import RecommendationService


class ValidationService:
    MAX_MONTHLY_QUANTITY = 100000

    def __init__(self) -> None:
        self.sku_repository = SKURepository()
        self.recommendation_service = RecommendationService()

    def validate_distributor_reply(
        self,
        distributor_code: str,
        reply_items: list[dict],
        recommended_skus: list[dict] | None = None,
    ) -> list[dict]:
        validation_result = self.validate_parsed_reply(
            {
                "distributor_code": distributor_code,
                "parsed_lines": [
                    {
                        "sku_code": item.get("sku_code"),
                        "monthly_quantity": item.get("monthly_quantity"),
                    }
                    for item in reply_items
                ],
            },
            recommended_skus=recommended_skus,
        )
        return validation_result["issues"]

    def validate_parsed_reply(
        self,
        parsed_reply: dict,
        recommended_skus: list[dict] | None = None,
    ) -> dict:
        distributor_code = (parsed_reply.get("distributor_code") or "").strip()
        normalized_lines = self._normalize_lines(parsed_reply)
        issues: list[dict] = []

        if not distributor_code:
            issues.append({
                "sku_code": None,
                "message": "distributor_code is required",
            })

        if not normalized_lines:
            issues.append({
                "sku_code": None,
                "message": "parsed_lines must not be empty",
            })

        sku_codes = [
            line["sku_code"]
            for line in normalized_lines
            if line["sku_code"]
        ]
        sku_lookup = self.sku_repository.get_skus_by_codes(sku_codes)
        recommended_sku_codes = self._get_recommended_sku_codes(distributor_code, recommended_skus)

        for line in normalized_lines:
            sku_code = line["sku_code"]
            quantity = line["monthly_quantity"]

            if not sku_code:
                issues.append({
                    "sku_code": None,
                    "message": "Each parsed line must include sku_code",
                })
                continue

            if quantity is None:
                issues.append({
                    "sku_code": sku_code,
                    "message": "Each parsed line must include monthly_quantity",
                })
                continue

            if quantity < 0:
                issues.append({
                    "sku_code": sku_code,
                    "message": "monthly_quantity cannot be negative",
                })
                continue

            if quantity == 0:
                issues.append({
                    "sku_code": sku_code,
                    "message": "monthly_quantity must be greater than 0",
                })
                continue

            if quantity > self.MAX_MONTHLY_QUANTITY:
                issues.append({
                    "sku_code": sku_code,
                    "message": (
                        f"monthly_quantity exceeds sanity threshold of "
                        f"{self.MAX_MONTHLY_QUANTITY}"
                    ),
                })

            if sku_code.upper() not in sku_lookup:
                issues.append({
                    "sku_code": sku_code,
                    "message": f"SKU '{sku_code}' does not exist in PostgreSQL",
                })
                continue

            if recommended_sku_codes is not None and sku_code.upper() not in recommended_sku_codes:
                issues.append({
                    "sku_code": sku_code,
                    "message": (
                        f"SKU '{sku_code}' is not part of the recommended set for distributor "
                        f"'{distributor_code}'"
                    ),
                })

        return {
            "distributor_code": distributor_code,
            "is_valid": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def _normalize_lines(parsed_reply: dict) -> list[dict]:
        raw_lines = parsed_reply.get("parsed_lines")
        if raw_lines is None:
            raw_lines = parsed_reply.get("sku_lines", [])

        normalized_lines: list[dict] = []
        for line in raw_lines or []:
            normalized_lines.append(
                {
                    "sku_code": str(line.get("sku_code") or "").strip().upper(),
                    "monthly_quantity": line.get("monthly_quantity", line.get("qty")),
                }
            )

        return normalized_lines

    def _get_recommended_sku_codes(
        self,
        distributor_code: str,
        recommended_skus: list[dict] | None,
    ) -> set[str] | None:
        if recommended_skus is not None:
            return {
                str(sku.get("sku_code", "")).strip().upper()
                for sku in recommended_skus
                if sku.get("sku_code")
            }

        if not distributor_code:
            return None

        try:
            recommendation_response = self.recommendation_service.get_sku_recommendations(
                distributor_code
            )
        except Exception:
            return None

        return {
            str(sku.get("sku_code", "")).strip().upper()
            for sku in recommendation_response.get("recommended_skus", [])
            if sku.get("sku_code")
        }
