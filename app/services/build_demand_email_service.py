class BuildDemandEmailService:
    
    def execute(self, distributor_context: dict, recommendation_response: dict):

        distributor_id = distributor_context["distributor_id"]
        distributor_name = distributor_context.get("distributor_name", distributor_id)

        # You can later make month dynamic
        month = "May 2026"

        recommendations = recommendation_response["recommendations"]

        # =====================
        # SUBJECT
        # =====================
        subject = f"Demand Confirmation Request – {distributor_id} – {month}"

        # =====================
        # BUILD TABLE
        # =====================
        table_lines = []
        table_lines.append("Recommended products — " + month)
        table_lines.append("─────────────────────────────────────────────────────────────────")
        table_lines.append("  Product Name                        SKU                Suggested Qty   Your Qty")
        table_lines.append("─────────────────────────────────────────────────────────────────")

        for item in recommendations:
            product_name = item["sku_name"]
            sku = item["sku_id"]

            # You can replace this later with ML / demand logic
            suggested_qty = item.get("score", 100)

            row = f"  {product_name[:30]:30}  {sku[:15]:15}  {str(int(suggested_qty)):10}   ______"
            table_lines.append(row)

        table_lines.append("─────────────────────────────────────────────────────────────────")

        table_block = "\n".join(table_lines)

        # =====================
        # BODY TEMPLATE
        # =====================
        body = f"""
To: Distributor {distributor_id} — {distributor_name}

Dear Partner,

Please suggest your demand quantities for the coming month ({month}). 
We have shared recommended products based on your sales history and graph-based relationships — kindly review and adjust quantities if needed.

You may reply directly to this email in the format:
SKU - Quantity

Example:
SKU001 - 120

{table_block}

Please confirm or share your revised quantities by 30 April 2026.

If you have any queries, feel free to reach out to your account manager.

Warm regards,
Demand Planning Team
"""

        return {
            "subject": subject,
            "body": body.strip()
        }