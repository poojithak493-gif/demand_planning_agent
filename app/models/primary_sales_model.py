from dataclasses import dataclass
from typing import Optional


@dataclass
class PrimarySalesRecord:
    sku_name: Optional[str] = None
    product_category_snapshot: Optional[str] = None
    priority_flag: Optional[str] = None
    distributor_id: Optional[int] = None
    gross_dispatch_value: Optional[float] = None
    transaction_date: Optional[str] = None