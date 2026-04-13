# app/services/build_demand_email_service.py

from app.core.constants import (
    DEMAND_WINDOW_DAYS,
    MANUFACTURER_COMPANY,
    MANUFACTURER_EMAIL,
    get_distributor_name,
)


class BuildDemandEmailService:
    """
    Builds the subject and body of the demand planning email
    that is sent from the Manufacturer to each Distributor.

    Inputs:
      - distributor_context    : output of FetchDistributorContextService
      - recommendation_response: output of SKURecommendationService

    Output dict:
      { "distributor_id", "subject", "body" }
    """

    def execute(self, distributor_context: dict, recommendation_response: dict) -> dict:
        distributor_id  = distributor_context["distributor_id"]
        recommendations = recommendation_response["recommendations"]

        # Index demand signals by sku_id for O(1) lookup in the table loop
        demand_signals = {
            row["sku_id"]: row
            for row in distributor_context.get("sku_demand_signals", [])
        }

        # Resolve human name from the registry (falls back gracefully)
        try:
            distributor_name = get_distributor_name(distributor_id)
        except ValueError:
            distributor_name = f"Distributor {distributor_id}"

        demand_window = DEMAND_WINDOW_DAYS

        # ── SUBJECT ──────────────────────────────────────────────────────────
        subject = (
            f"[Demand Planning] Forecast Request for {distributor_id} "
            f"— Next {demand_window} Days"
        )

        # ── BODY ─────────────────────────────────────────────────────────────
        lines = [
            f"Dear {distributor_name} ({distributor_id}),",
            "",
            f"This is your monthly demand forecast request from {MANUFACTURER_COMPANY}.",
            (
                f"Kindly confirm your expected stock requirements "
                f"for the next {demand_window} days."
            ),
            "",
            "=" * 62,
            "  RECOMMENDED SKUs FOR YOUR REVIEW",
            "=" * 62,
            "",
            "The following products have been selected based on your",
            "purchase history and our current product catalogue.",
            "",
            f"{'No.':<4} {'SKU ID':<14} {'Product Name':<32} {'Your Avg Qty':>12}",
            f"{'─'*4} {'─'*14} {'─'*32} {'─'*12}",
        ]

        # Recommended products — one row per SKU
        for i, item in enumerate(recommendations, start=1):
            sku_id   = item.get("sku_id", "N/A")
            sku_name = item.get("sku_name", "N/A")
            signal   = demand_signals.get(sku_id, {})
            avg_qty  = signal.get("avg_quantity")
            avg_str  = f"{avg_qty} units" if avg_qty else "First order"

            lines.append(
                f"{str(i):<4} {sku_id:<14} {sku_name:<32} {avg_str:>12}"
            )

        lines.extend([
            "",
            "=" * 62,
            "  HOW TO RESPOND",
            "=" * 62,
            "",
            "Please reply to this email with your confirmed quantities",
            "in the format below (one SKU per line):",
            "",
            "    SKU_ID - QUANTITY",
            "",
            "Example:",
            "    SKU001 - 150",
            "    SKU002 - 300",
            "    SKU009 - 75",
            "",
            "You may also attach an Excel file (.xlsx) with two columns:",
            "    Column A : SKU ID",
            "    Column B : Quantity",
            "",
            "Please respond within 5 business days.",
            "",
            "For any queries, reply to this email or contact us at:",
            f"    {MANUFACTURER_EMAIL}",
            "",
            "─" * 62,
            f"Regards,",
            f"{MANUFACTURER_COMPANY}",
            f"Reply-To: {MANUFACTURER_EMAIL}",
        ])

        return {
            "distributor_id": distributor_id,
            "subject": subject,
            "body": "\n".join(lines),
        }