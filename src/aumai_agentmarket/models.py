"""Pydantic models for aumai-agentmarket."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AgentListing(BaseModel):
    """A marketplace listing for a pre-built agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent.")
    name: str = Field(..., description="Human-readable agent name.")
    description: str = Field(..., description="What the agent does.")
    version: str = Field(default="1.0.0", description="Semantic version string.")
    author: str = Field(..., description="Author or organisation name.")
    capabilities: list[str] = Field(
        default_factory=list,
        description="Functional capabilities the agent provides.",
    )
    tags: list[str] = Field(default_factory=list, description="Free-form search tags.")
    downloads: int = Field(default=0, ge=0, description="Total download count.")
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Mean star rating.")
    license: str = Field(..., description="SPDX license identifier or name.")
    install_command: str = Field(
        ..., description="Shell command to install the agent."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of listing creation.",
    )


class AgentReview(BaseModel):
    """A user review for an agent listing."""

    reviewer: str = Field(..., description="Username or display name of the reviewer.")
    rating: float = Field(..., ge=0.0, le=5.0, description="Star rating (0–5).")
    comment: str = Field(default="", description="Optional review text.")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the review.",
    )


class SearchFilter(BaseModel):
    """Filter parameters for agent catalog search."""

    query: str | None = Field(None, description="Substring to match in name/description.")
    capabilities: list[str] | None = Field(
        None, description="Required capabilities (all must match)."
    )
    min_rating: float | None = Field(
        None, ge=0.0, le=5.0, description="Minimum acceptable rating."
    )
    tags: list[str] | None = Field(
        None, description="Required tags (all must match)."
    )

    @field_validator("min_rating")
    @classmethod
    def validate_min_rating(cls, value: float | None) -> float | None:
        """Ensure min_rating is within [0, 5]."""
        if value is not None and not (0.0 <= value <= 5.0):
            raise ValueError("min_rating must be between 0.0 and 5.0.")
        return value


__all__ = [
    "AgentListing",
    "AgentReview",
    "SearchFilter",
]
