from typing import List
from pydantic import BaseModel, Field, model_validator


class DistributorContextResponse(BaseModel):
    distributor_id: str
    distributor_code: str
    name: str
    email: str
    phone: str | None = None
    region: str | None = None
    priority: str
    is_active: bool


class SKURecommendationItem(BaseModel):
    sku_id: str
    sku_code: str
    sku_name: str
    category: str | None = None
    score: int
    reason: str


class SKURecommendationResponse(BaseModel):
    distributor_code: str
    distributor_name: str
    recommended_skus: List[SKURecommendationItem]


class DemandPlanResponse(BaseModel):
    distributor: DistributorContextResponse
    recommended_skus: List[SKURecommendationItem]


class EmailRecommendationItem(BaseModel):
    sku_id: str
    sku_code: str
    sku_name: str
    category: str | None = None
    score: int
    reason: str
    recommended_monthly_quantity: int


class RecommendationEmailPayloadResponse(BaseModel):
    distributor_code: str
    distributor_name: str
    email_subject: str
    email_body: str
    recommended_skus: List[SKURecommendationItem]


class ParsedReplyItem(BaseModel):
    sku_code: str = Field(..., min_length=1)
    monthly_quantity: int = Field(..., ge=0)


class ParsedReplyRequest(BaseModel):
    distributor_code: str
    confirmed_by: str = Field(..., min_length=1)
    notes: str | None = None
    raw_reply_text: str | None = None
    items: List[ParsedReplyItem] | None = None

    @model_validator(mode="after")
    def validate_unique_sku_codes(self) -> "ParsedReplyRequest":
        if self.raw_reply_text is None and not self.items:
            raise ValueError("Either raw_reply_text or items must be provided")

        if self.raw_reply_text is not None and not self.raw_reply_text.strip():
            raise ValueError("raw_reply_text must not be blank")

        if self.items:
            sku_codes = [item.sku_code for item in self.items]
            if len(sku_codes) != len(set(sku_codes)):
                raise ValueError("Duplicate sku_code values are not allowed in reply items")

        return self


class ReplyValidationIssue(BaseModel):
    sku_code: str | None = None
    message: str


class ProcessReplyRequest(BaseModel):
    email_body: str = Field(..., min_length=1)


class WeeklyPlanItem(BaseModel):
    sku_code: str
    monthly_quantity: int
    week1_qty: int
    week2_qty: int
    week3_qty: int
    week4_qty: int


class ReplyProcessingResponse(BaseModel):
    distributor_code: str
    distributor_name: str
    confirmed_by: str
    notes: str | None = None
    is_valid: bool
    issues: List[ReplyValidationIssue]
    weekly_plan: List[WeeklyPlanItem]
