"""FastAPI application for aumai-agentmarket."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from aumai_agentmarket.core import AgentCatalog, AgentNotFoundError
from aumai_agentmarket.models import AgentListing, AgentReview, SearchFilter

app = FastAPI(
    title="AumAI Agent Marketplace",
    description="API for browsing and publishing pre-built agents.",
    version="0.1.0",
)

# Application-level catalog instance.
_catalog = AgentCatalog()


@app.get(
    "/api/agents",
    response_model=list[AgentListing],
    summary="List or search agents",
)
def list_agents(
    query: str | None = None,
    min_rating: float | None = None,
    tag: str | None = None,
    capability: str | None = None,
) -> list[AgentListing]:
    """Return agents matching the given search filters.

    All query parameters are optional.  When omitted, all agents are returned.
    """
    search_filter = SearchFilter(
        query=query,
        min_rating=min_rating,
        tags=[tag] if tag else None,
        capabilities=[capability] if capability else None,
    )
    return _catalog.search(search_filter)


@app.get(
    "/api/agents/trending",
    response_model=list[AgentListing],
    summary="Trending agents",
)
def trending_agents(limit: int = 10) -> list[AgentListing]:
    """Return the most-downloaded agents."""
    return _catalog.trending(limit=limit)


@app.get(
    "/api/agents/{agent_id}",
    response_model=AgentListing,
    summary="Get agent by ID",
)
def get_agent(agent_id: str) -> AgentListing:
    """Return a single agent listing by its unique ID."""
    try:
        return _catalog.get(agent_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found.",
        ) from None


@app.post(
    "/api/agents",
    response_model=AgentListing,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a new agent",
)
def publish_agent(listing: AgentListing) -> AgentListing:
    """Register a new agent listing in the marketplace."""
    _catalog.register(listing)
    return listing


@app.post(
    "/api/agents/{agent_id}/reviews",
    response_model=AgentReview,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review",
)
def add_review(agent_id: str, review: AgentReview) -> AgentReview:
    """Submit a review for the specified agent."""
    try:
        _catalog.add_review(agent_id, review)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found.",
        ) from None
    return review


__all__ = ["app"]
