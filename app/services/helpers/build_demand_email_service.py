class BuildDemandEmailService:
    def execute(self, distributor_context: dict, recommendation_response: dict) -> dict:
        distributor_code = distributor_context["distributor_code"]
        recommendations = recommendation_response["recommendations"]

        subject = f"Demand Planning Request for Distributor {distributor_code}"

        lines = [
            f"Dear Distributor {distributor_code},",
            "",
            "Please confirm your expected demand for the next 30 days.",
            "Based on your purchase graph, we suggest the following SKUs:",
            ""
        ]

        for item in recommendations:
            lines.append(f"{item['sku_code']} - {item['sku_name']}")

        lines.extend([
            "",
            "Please reply in this format:",
            "SKU11 - 100",
            "SKU12 - 200",
            "",
            "Regards,",
            "Demand Planning Team"
        ])

        return {
            "subject": subject,
            "body": "\n".join(lines)
        }
