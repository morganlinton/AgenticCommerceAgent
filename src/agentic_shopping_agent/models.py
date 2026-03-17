from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShoppingCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="The user requirement to evaluate.")
    kind: Literal["preference", "must_have", "avoid"] = Field(
        description="How strongly the requirement should influence the final recommendation."
    )
    weight: float = Field(
        default=1.0,
        ge=0.5,
        le=3.0,
        description="Relative weight used in local ranking.",
    )


class ShoppingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(description="What the user wants to buy.")
    criteria: list[ShoppingCriterion] = Field(default_factory=list)
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Upper budget limit in the preferred currency, if provided.",
    )
    currency: str = Field(default="USD", description="Preferred currency code.")
    location: str = Field(default="United States", description="Shopper location.")
    max_options: int = Field(default=4, ge=2, le=8)
    notes: Optional[str] = Field(
        default=None,
        description="Extra context that should influence the browsing task.",
    )
    allowed_domains: list[str] = Field(default_factory=list)
    allow_open_web: bool = Field(
        default=False,
        description="Whether the agent may browse beyond the built-in trusted domain allowlist.",
    )
    proxy_country_code: Optional[str] = Field(
        default=None,
        description="Optional Browser Use proxy country override such as us, gb, or de.",
    )


class CriterionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_name: str = Field(description="The matching criterion from the request.")
    score: int = Field(
        ge=0,
        le=10,
        description="0 means poor fit, 10 means excellent fit.",
    )
    evidence: str = Field(description="Short factual explanation for the score.")


class ProductOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Product name.")
    retailer: str = Field(description="The seller or primary source.")
    product_url: str = Field(description="Direct URL to the product page.")
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Current listed price if available.",
    )
    currency: Optional[str] = Field(
        default=None,
        description="Currency code for the listed price.",
    )
    availability: Optional[str] = Field(
        default=None,
        description="Availability signal such as In Stock, Preorder, or Unknown.",
    )
    rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=5,
        description="Average review rating if available.",
    )
    review_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of reviews if available.",
    )
    summary: str = Field(description="What makes the product notable.")
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    criterion_assessments: list[CriterionAssessment] = Field(default_factory=list)
    source_urls: list[str] = Field(
        default_factory=list,
        description="URLs used to support this option, including review pages when possible.",
    )
    confidence_notes: Optional[str] = Field(
        default=None,
        description="Uncertainty, missing data, or caveats for this option.",
    )


class ShoppingResearch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_summary: str = Field(description="Short summary of the market scan.")
    options: list[ProductOption] = Field(
        min_length=2,
        description="Distinct purchasable product options found during browsing.",
    )
    notable_tradeoffs: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class ProductVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(description="Product name being re-checked.")
    product_url: str = Field(description="Product URL that was revisited.")
    retailer: Optional[str] = Field(
        default=None,
        description="Retailer confirmed during verification.",
    )
    product_still_matches: bool = Field(
        description="Whether the revisited page still clearly matches the originally researched product."
    )
    verified_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Current verified price if available.",
    )
    verified_currency: Optional[str] = Field(
        default=None,
        description="Currency code for the verified price.",
    )
    verified_availability: Optional[str] = Field(
        default=None,
        description="Current availability signal from the verification pass.",
    )
    price_matches_original: Optional[bool] = Field(
        default=None,
        description="Whether the current price still matches the original research closely enough.",
    )
    availability_matches_original: Optional[bool] = Field(
        default=None,
        description="Whether the current availability still matches the original research.",
    )
    notes: str = Field(description="Short explanation of what verification found.")
    source_urls: list[str] = Field(
        default_factory=list,
        description="URLs revisited during verification.",
    )


class VerificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(description="Short summary of what changed or was confirmed.")
    checks: list[ProductVerification] = Field(
        default_factory=list,
        description="Verification checks for the top candidate products.",
    )
    missing_information: list[str] = Field(default_factory=list)


class RankedOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: ProductOption
    total_score: float = Field(description="Local computed score out of 100.")
    criterion_score: float = Field(description="Criterion fit component.")
    budget_score: float = Field(description="Budget fit component.")
    quality_score: float = Field(description="Quality signal component.")
    trust_score: float = Field(description="Source completeness component.")
    verification_score: float = Field(description="Final verification component.")
    rationale: list[str] = Field(default_factory=list)
    verification: Optional[ProductVerification] = None


class ComparisonCriterionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_name: str
    criterion_kind: Literal["preference", "must_have", "avoid"]
    score: Optional[int] = Field(default=None, ge=0, le=10)
    evidence: Optional[str] = None


class ComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    product_name: str
    retailer: str
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    availability: Optional[str] = None
    total_score: float
    criterion_score: float
    budget_score: float
    quality_score: float
    trust_score: float
    verification_score: float
    verification_status: Literal["verified", "changed", "uncertain", "not_run"]
    verification_notes: Optional[str] = None
    source_count: int = Field(ge=0)
    criterion_breakdown: list[ComparisonCriterionRow] = Field(default_factory=list)


class PurchaseDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: ShoppingRequest
    research_summary: str
    recommended_option: RankedOption
    alternatives: list[RankedOption] = Field(default_factory=list)
    comparison_rows: list[ComparisonRow] = Field(default_factory=list)
    final_answer: str
    notable_tradeoffs: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    verification_summary: Optional[str] = None
    live_url: Optional[str] = None
