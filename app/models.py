from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    language: str = Field(default="python")
    code: str = Field(min_length=1, max_length=200_000)


class Finding(BaseModel):
    rule_id: str
    severity: str
    category: str
    line: int
    message: str
    remediation: str


class ReviewResponse(BaseModel):
    score: int
    summary: str
    findings: list[Finding]
