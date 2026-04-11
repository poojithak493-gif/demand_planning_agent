class ValidationService:
    @staticmethod
    def validate_distributor_context(data: dict) -> dict:
        required_fields = [
            "distributor_id",
            "name",
            "region",
            "channel",
            "recent_order_volume",
            "priority",
        ]

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required distributor fields: {', '.join(missing_fields)}")

        return data

    @staticmethod
    def validate_sku_data(data: dict) -> dict:
        required_fields = [
            "sku_id",
            "sku_name",
            "regions",
            "channels",
            "base_score",
        ]

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required SKU fields: {', '.join(missing_fields)}")

        return data