from typing import Literal

from pydantic import BaseModel, Field, model_validator

Severity = Literal["critical", "major", "minor", "nit"]
Category = Literal["bug", "security", "performance", "style", "missing_tests"]


class ReviewRequest(BaseModel):
    pr_url: str | None = Field(default=None, max_length=2048)
    diff: str | None = Field(default=None, max_length=2_000_000)
    consent_to_ai_processing: bool

    @model_validator(mode="after")
    def validate_source(self) -> "ReviewRequest":
        if bool(self.pr_url) == bool(self.diff):
            raise ValueError("Provide exactly one of pr_url or diff.")
        if not self.consent_to_ai_processing:
            raise ValueError("Consent to Google AI Studio processing is required.")
        return self


class Finding(BaseModel):
    severity: Severity
    category: Category
    file: str = Field(min_length=1, max_length=500)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=300)
    explanation: str = Field(min_length=1, max_length=5000)
    suggested_fix: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def validate_line_range(self) -> "Finding":
        if self.line_end < self.line_start:
            raise ValueError("line_end must be greater than or equal to line_start")
        return self


class ReviewResult(BaseModel):
    id: str
    title: str
    summary: str
    findings: list[Finding]
    changed_files: list[str]
    excluded_files: list[str] = []
    processed_changed_lines: int
    diff: str | None = None


class ReviewPayload(BaseModel):
    summary: str
    findings: list[Finding]
