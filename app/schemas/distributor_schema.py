from typing import List
from pydantic import BaseModel


class DistributorContextResponse(BaseModel):
    distributor_id: str
    name: str
    region: str
    channel: str
    recent_order_volume: int
    priority: str


class SKURecommendationItem(BaseModel):
    sku_id: str
    sku_name: str
    score: int
    reason: str


class SKURecommendationResponse(BaseModel):
    distributor_id: str
    distributor_name: str
    recommended_skus: List[SKURecommendationItem]