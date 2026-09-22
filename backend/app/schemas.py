from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Idea(Strict):
    id: str
    title: str
    target_customer: str
    problem: str
    proposed_service: str
    supporting_source_ids: list[str]
    counterevidence_source_ids: list[str]
    assumptions: list[str]
    open_questions: list[str]
    target_profile_fit: str


class Ideas(Strict):
    ideas: list[Idea] = Field(min_length=2, max_length=3)


class CardContent(Strict):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=8000)
    target_customer: str
    benefit: str
    deliverables: str
    exclusions: str
    prerequisites: str
    phases: str
    pricing_model: str
    price_rationale: str
    source_ids: list[str]
    open_questions: list[str]


class CardEdit(CardContent):
    hours: Decimal | None = Field(default=None, gt=0, le=10000)
    hourly_rate: Decimal | None = Field(default=None, gt=0, le=10000)
    expected_version: int = Field(ge=1)


class VersionRequest(Strict):
    expected_version: int = Field(ge=1)


class AnalyzeRequest(Strict):
    mode: Literal['live', 'example']


class CreateCardRequest(Strict):
    run_id: str
    idea_id: str


class ProfileRequest(Strict):
    text: str = Field(min_length=10, max_length=3000)

