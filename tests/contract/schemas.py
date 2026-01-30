"""Pydantic schemas for API contract validation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, RootModel, field_validator


class AnalyzeResponseSchema(BaseModel):
    """Schema for POST /api/analyze response."""
    report_id: str = Field(..., description="UUID of the created report")


class CheckFindingSchema(BaseModel):
    """Schema for a single check finding."""
    id: str
    name: str
    status: Literal["pass", "warn", "fail"]
    evidence: dict[str, Any] = Field(
        ...,
        description="File path and snippet; optional start_line, end_line (int) for code analysis",
    )
    recommendation: str
    points: int


class SectionFindingSchema(BaseModel):
    """Schema for a section with checks."""
    name: str
    checks: list[CheckFindingSchema]
    score: int


class ReportFindingsSuccessSchema(BaseModel):
    """Schema for successful report findings."""
    overall_score: int = Field(..., ge=0, le=100)
    sections: list[SectionFindingSchema]
    interview_pack: list[str] = Field(default_factory=list)


class ReportFindingsFailedSchema(BaseModel):
    """Schema for failed report findings."""
    error: str


class ReportResponseSchema(BaseModel):
    """Schema for GET /api/reports/{id} response."""
    id: str = Field(..., description="UUID of the report")
    repo_url: str
    repo_owner: str | None = None
    repo_name: str | None = None
    commit_sha: str | None = None
    status: Literal["pending", "done", "failed"] | None = None
    overall_score: int | None = Field(None, ge=0, le=100)
    findings_json: dict[str, Any] | list | None = None
    created_at: str | None = Field(None, description="ISO 8601 datetime")
    updated_at: str | None = Field(None, description="ISO 8601 datetime")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        if v is not None and v not in ("pending", "done", "failed"):
            raise ValueError(f"status must be 'pending', 'done', or 'failed', got '{v}'")
        return v


class ReportListItemSchema(BaseModel):
    """Schema for GET /api/reports list item."""
    id: str
    repo_url: str
    score: int | None = Field(None, ge=0, le=100)
    created_at: str | None = Field(None, description="ISO 8601 datetime")


class ReportListResponseSchema(RootModel):
    """Schema for GET /api/reports response."""
    root: list[ReportListItemSchema]


class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    detail: str
