"""Shared test fixtures for aumai-agentmarket."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aumai_agentmarket.models import AgentListing, AgentReview, SearchFilter


@pytest.fixture()
def code_review_agent() -> AgentListing:
    return AgentListing(
        agent_id="code-review-v1",
        name="Code Review Agent",
        description="Automated code review with AI-powered suggestions.",
        version="1.2.0",
        author="AumAI Labs",
        capabilities=["code-review", "linting", "suggestions"],
        tags=["code", "review", "automation"],
        downloads=1500,
        rating=4.2,
        license="MIT",
        install_command="pip install aumai-code-review",
    )


@pytest.fixture()
def doc_agent() -> AgentListing:
    return AgentListing(
        agent_id="doc-writer-v1",
        name="Documentation Writer",
        description="Generates technical documentation from code.",
        version="2.0.0",
        author="DocBot Inc",
        capabilities=["documentation", "markdown"],
        tags=["docs", "writing"],
        downloads=800,
        rating=3.8,
        license="Apache-2.0",
        install_command="pip install aumai-doc-writer",
    )


@pytest.fixture()
def agent_review() -> AgentReview:
    return AgentReview(
        reviewer="test-user",
        rating=5.0,
        comment="Excellent agent, very accurate!",
    )


@pytest.fixture()
def agent_config_file(
    tmp_path: Path, code_review_agent: AgentListing
) -> Path:
    config_file = tmp_path / "agent.json"
    config_file.write_text(
        code_review_agent.model_dump_json(), encoding="utf-8"
    )
    return config_file
