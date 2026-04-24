from typing import List
from app.data.sku_data import get_sku_id_to_name


def get_recommended_products(limit: int = 5) -> List[str]:
    sku_id_to_name = get_sku_id_to_name()
    if not sku_id_to_name:
        return []
    return list(sku_id_to_name.values())[:limit]


def build_demand_email(distributor_id: str, distributor_email: str) -> dict:
    recommended_products = get_recommended_products(limit=5)

    if recommended_products:
        recommended_block = "\n".join(
            f"{i}. {product}"
            for i, product in enumerate(recommended_products, start=1)
        )
    else:
        recommended_block = "1. No products available"

    subject = "Demand Request for Upcoming Month"

    body = f"""Dear Distributor,

Greetings from Lipton Enterprises.

We are planning for the upcoming month and request you to share your expected product demand.

Your Distributor ID: {distributor_id}

Best Recommended Products:
{recommended_block}

Please provide the expected demand for the next month in the following format:

Product Name - Quantity

Example:
Product A - 100
Product B - 250

You may also fill in the attached Excel file and reply back to this email.

Regards,
Lipton Enterprises
"""

    return {
        "to_email": distributor_email,
        "subject": subject,
        "body": body
    }