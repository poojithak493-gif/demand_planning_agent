class BuildDemandEmailService:
    
    def execute(self, distributor_context: dict, recommendations: list):

        distributor_id = distributor_context["distributor_id"]
        distributor_name = distributor_context.get("distributor_name", distributor_id)

        month = "May 2026"

        subject = f"Demand Confirmation Request – {distributor_id} – {month}"

        table_lines = []
        table_lines.append("Recommended products — " + month)
        table_lines.append("────────────────────────────────────────────────────────────────────────────")
        table_lines.append("  Product Name                                 Reason")
        table_lines.append("────────────────────────────────────────────────────────────────────────────")

        for item in recommendations:
            product_name = item.get("product", "")
            reason = item.get("reason", "")

            row = f"  {product_name[:40]:40}  {reason[:30]}"
            table_lines.append(row)

        table_lines.append("────────────────────────────────────────────────────────────────────────────")

        table_block = "\n".join(table_lines)

        body = f"""
To: Distributor {distributor_id} — {distributor_name}

Dear Partner,

Please review the following recommended new products for the coming month ({month}).

These recommendations are shared based on distributor fit, product category relevance, and channel suitability.
Kindly reply with the products you are interested in and the required quantities.

You may reply directly to this email in the format:
Product Name - Quantity

Example:
MALKIST CHEESE DISPLAY BOX - 20
MALKIST CHEESE MULTIPACK - 15

{table_block}

Please confirm or share your required quantities.

Warm regards,
Demand Planning Team
"""

        return {
            "subject": subject,
            "body": body.strip()
        }