"""CLI entry point for aumai-agentmarket."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from aumai_agentmarket.core import AgentCatalog, AgentNotFoundError
from aumai_agentmarket.models import AgentListing, SearchFilter

_catalog = AgentCatalog()


@click.group()
@click.version_option()
def main() -> None:
    """AumAI Agent Marketplace — discover and publish pre-built agents."""


@main.command("search")
@click.option("--query", default=None, help="Text search query.")
@click.option("--min-rating", default=None, type=float, help="Minimum star rating.")
@click.option(
    "--capability", "capabilities", multiple=True, help="Required capability (repeatable)."
)
@click.option("--tag", "tags", multiple=True, help="Required tag (repeatable).")
def search_command(
    query: str | None,
    min_rating: float | None,
    capabilities: tuple[str, ...],
    tags: tuple[str, ...],
) -> None:
    """Search the agent marketplace.

    Example: aumai-agentmarket search --query "code review"
    """
    search_filter = SearchFilter(
        query=query,
        min_rating=min_rating,
        capabilities=list(capabilities) if capabilities else None,
        tags=list(tags) if tags else None,
    )
    results = _catalog.search(search_filter)

    if not results:
        click.echo("No agents found matching the given criteria.")
        return

    for listing in results:
        click.echo(
            f"[{listing.agent_id}] {listing.name} v{listing.version}"
            f" — Rating: {listing.rating:.1f}/5.0  Downloads: {listing.downloads}"
        )
        click.echo(f"  {listing.description}")
        click.echo(f"  Install: {listing.install_command}")
        click.echo()


@main.command("publish")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to a JSON config file with AgentListing fields.",
)
def publish_command(config_path: str) -> None:
    """Publish an agent from a config file.

    Example: aumai-agentmarket publish --config agent.json
    """
    raw_text = Path(config_path).read_text(encoding="utf-8")
    try:
        data: object = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        click.echo(f"Invalid JSON: {exc}", err=True)
        sys.exit(1)

    if not isinstance(data, dict):
        click.echo("Config must be a JSON object.", err=True)
        sys.exit(1)

    try:
        listing = AgentListing.model_validate(data)
    except Exception as exc:
        click.echo(f"Validation error: {exc}", err=True)
        sys.exit(1)

    _catalog.register(listing)
    click.echo(f"Agent '{listing.agent_id}' published successfully.")


@main.command("serve")
@click.option("--port", default=8000, show_default=True, help="HTTP port to listen on.")
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind address.")
def serve_command(port: int, host: str) -> None:
    """Start the FastAPI marketplace server.

    Example: aumai-agentmarket serve --port 8000
    """
    try:
        import uvicorn  # type: ignore[import-untyped]
    except ImportError:
        click.echo(
            "uvicorn is required to run the server. Install it with: pip install uvicorn",
            err=True,
        )
        sys.exit(1)

    click.echo(f"Starting Agent Marketplace server on {host}:{port} ...")
    uvicorn.run("aumai_agentmarket.api:app", host=host, port=port, reload=False)


@main.command("top-rated")
@click.option("--limit", default=10, show_default=True, help="Number of results.")
def top_rated_command(limit: int) -> None:
    """Show top-rated agents.

    Example: aumai-agentmarket top-rated --limit 5
    """
    results = _catalog.top_rated(limit=limit)
    if not results:
        click.echo("No agents registered.")
        return
    for listing in results:
        click.echo(
            f"[{listing.agent_id}] {listing.name}  Rating: {listing.rating:.1f}/5.0"
        )


@main.command("get")
@click.argument("agent_id")
def get_command(agent_id: str) -> None:
    """Show full details for an agent by ID.

    Example: aumai-agentmarket get code-review-agent-v1
    """
    try:
        listing = _catalog.get(agent_id)
    except AgentNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(json.dumps(listing.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
