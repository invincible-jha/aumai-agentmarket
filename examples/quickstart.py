"""Quickstart examples for aumai-agentmarket.

Demonstrates the agent marketplace catalog: publishing listings, searching by
text and capability, writing reviews, checking ratings, and browsing leaderboards.

Run this file directly to verify your installation:

    python examples/quickstart.py

Each demo function is self-contained and prints its own output.
"""

from __future__ import annotations

from aumai_agentmarket import (
    AgentCatalog,
    AgentListing,
    AgentNotFoundError,
    AgentReview,
    SearchFilter,
)


# ---------------------------------------------------------------------------
# Shared catalog fixtures
# ---------------------------------------------------------------------------


def build_sample_catalog() -> AgentCatalog:
    """Create and populate a catalog with several agent listings for demos."""
    catalog = AgentCatalog()

    agents = [
        AgentListing(
            agent_id="code-review-agent-v2",
            name="Code Review Agent",
            description="Automated code review covering security vulnerabilities, style violations, and algorithmic complexity.",
            version="2.1.0",
            author="AumAI Engineering",
            capabilities=["code_review", "security_analysis", "style_check", "complexity_analysis"],
            tags=["code", "devops", "security", "ci-cd"],
            downloads=8_450,
            rating=4.7,
            license="Apache-2.0",
            install_command="pip install aumai-agent-code-review",
        ),
        AgentListing(
            agent_id="invoice-parser-v3",
            name="Invoice Parser Agent",
            description="Extracts structured data from PDF and scanned image invoices, including line items, totals, and vendor information.",
            version="3.0.1",
            author="AumAI Finance Team",
            capabilities=["pdf_parsing", "ocr", "structured_output", "entity_extraction"],
            tags=["finance", "invoices", "ocr", "enterprise"],
            downloads=12_200,
            rating=4.5,
            license="Apache-2.0",
            install_command="pip install aumai-agent-invoice-parser",
        ),
        AgentListing(
            agent_id="sql-query-agent-v1",
            name="SQL Query Agent",
            description="Translates natural language questions into optimized SQL queries with schema introspection.",
            version="1.4.0",
            author="AumAI Data Team",
            capabilities=["text_to_sql", "schema_introspection", "query_optimization"],
            tags=["sql", "database", "analytics", "enterprise"],
            downloads=5_800,
            rating=4.3,
            license="MIT",
            install_command="pip install aumai-agent-sql",
        ),
        AgentListing(
            agent_id="doc-summarizer-v1",
            name="Document Summarizer Agent",
            description="Produces executive briefings from long documents with key points, risks, and action items.",
            version="1.0.0",
            author="AumAI Research",
            capabilities=["document_summarization", "structured_output", "risk_extraction"],
            tags=["nlp", "summarization", "enterprise"],
            downloads=980,
            rating=4.1,
            license="Apache-2.0",
            install_command="pip install aumai-agent-summarizer",
        ),
        AgentListing(
            agent_id="web-scraper-v2",
            name="Web Scraper Agent",
            description="Scrapes and parses web pages including JavaScript-rendered content into structured JSON.",
            version="2.0.0",
            author="AumAI Web Team",
            capabilities=["web_scraping", "html_parsing", "structured_output", "js_rendering"],
            tags=["web", "scraping", "data-collection"],
            downloads=15_600,
            rating=4.6,
            license="Apache-2.0",
            install_command="pip install aumai-agent-web-scraper",
        ),
    ]

    for agent in agents:
        catalog.register(agent)

    return catalog


# ---------------------------------------------------------------------------
# Demo 1: Publish and retrieve agents
# ---------------------------------------------------------------------------


def demo_publish_and_retrieve(catalog: AgentCatalog) -> None:
    """Show how to publish a new agent and retrieve its details."""
    print("=" * 60)
    print("DEMO 1: Publish and Retrieve Agents")
    print("=" * 60)

    # Publish a new agent
    new_agent = AgentListing(
        agent_id="rag-retrieval-agent-v1",
        name="RAG Retrieval Agent",
        description="Performs dense vector retrieval over document corpora with reranking and citation extraction.",
        version="1.0.0",
        author="AumAI RAG Team",
        capabilities=["vector_retrieval", "reranking", "citation_extraction"],
        tags=["rag", "retrieval", "nlp"],
        license="Apache-2.0",
        install_command="pip install aumai-agent-rag-retrieval",
    )
    catalog.register(new_agent)
    print(f"  Published: [{new_agent.agent_id}] {new_agent.name}")

    # Retrieve by ID
    fetched = catalog.get("rag-retrieval-agent-v1")
    print(f"  Retrieved: {fetched.name} v{fetched.version}")
    print(f"  Author: {fetched.author}")
    print(f"  Capabilities: {', '.join(fetched.capabilities)}")
    print(f"  Install: {fetched.install_command}")

    # Expect AgentNotFoundError for unknown ID
    try:
        catalog.get("nonexistent-agent-xyz")
    except AgentNotFoundError as exc:
        print(f"\n  AgentNotFoundError: {exc}")

    print()


# ---------------------------------------------------------------------------
# Demo 2: Multi-criteria search
# ---------------------------------------------------------------------------


def demo_search(catalog: AgentCatalog) -> None:
    """Show text search, capability filtering, minimum rating, and tag filtering."""
    print("=" * 60)
    print("DEMO 2: Multi-Criteria Search")
    print("=" * 60)

    # 1. Text search only
    results = catalog.search(SearchFilter(query="document"))
    print(f"  query='document' → {len(results)} result(s):")
    for agent in results:
        print(f"    [{agent.agent_id}] {agent.name} (rating: {agent.rating})")

    # 2. Capability filter (all must match)
    results = catalog.search(SearchFilter(capabilities=["structured_output", "ocr"]))
    print(f"\n  capabilities=['structured_output','ocr'] → {len(results)} result(s):")
    for agent in results:
        print(f"    [{agent.agent_id}] {agent.name}")

    # 3. Minimum rating gate
    results = catalog.search(SearchFilter(min_rating=4.5))
    print(f"\n  min_rating=4.5 → {len(results)} result(s):")
    for agent in results:
        print(f"    [{agent.agent_id}] rating={agent.rating}")

    # 4. Tag filter
    results = catalog.search(SearchFilter(tags=["enterprise"]))
    print(f"\n  tags=['enterprise'] → {len(results)} result(s):")
    for agent in results:
        print(f"    [{agent.agent_id}] {agent.name}")

    # 5. Combined filter
    results = catalog.search(SearchFilter(
        query="agent",
        capabilities=["structured_output"],
        min_rating=4.0,
        tags=["enterprise"],
    ))
    print(f"\n  Combined filter → {len(results)} result(s):")
    for agent in results:
        print(f"    [{agent.agent_id}] {agent.name} (rating: {agent.rating})")

    print()


# ---------------------------------------------------------------------------
# Demo 3: Review system and rating updates
# ---------------------------------------------------------------------------


def demo_reviews_and_ratings(catalog: AgentCatalog) -> None:
    """Show how reviews accumulate and the mean rating updates automatically."""
    print("=" * 60)
    print("DEMO 3: Review System and Rating Updates")
    print("=" * 60)

    target_id = "sql-query-agent-v1"
    listing = catalog.get(target_id)
    print(f"  Agent: {listing.name}")
    print(f"  Initial rating: {listing.rating}/5.0 (set on publish)")

    # Add three reviews
    reviews = [
        AgentReview(
            reviewer="data_engineer_alice",
            rating=4.9,
            comment="Generates correct SQL 95% of the time. Handles complex JOINs well.",
        ),
        AgentReview(
            reviewer="analyst_bob",
            rating=4.2,
            comment="Great for standard analytics queries. Struggles with window functions.",
        ),
        AgentReview(
            reviewer="dba_carol",
            rating=3.8,
            comment="Acceptable for prototyping. Would not use in production without review.",
        ),
    ]

    for review in reviews:
        catalog.add_review(target_id, review)
        updated = catalog.get(target_id)
        print(f"  After review from {review.reviewer}: rating={updated.rating}/5.0")

    # Display all reviews
    all_reviews = catalog.get_reviews(target_id)
    print(f"\n  All reviews for '{target_id}' ({len(all_reviews)} total):")
    for review in all_reviews:
        print(f"    {review.reviewer}: {review.rating}/5  \"{review.comment[:50]}...\"")

    print()


# ---------------------------------------------------------------------------
# Demo 4: Leaderboards and trending
# ---------------------------------------------------------------------------


def demo_leaderboards(catalog: AgentCatalog) -> None:
    """Show top-rated and trending agent listings."""
    print("=" * 60)
    print("DEMO 4: Leaderboards and Trending")
    print("=" * 60)

    # Top-rated
    top = catalog.top_rated(limit=3)
    print("  Top 3 by rating:")
    for rank, agent in enumerate(top, start=1):
        print(f"    #{rank}  [{agent.agent_id}] {agent.name} — {agent.rating:.1f}/5.0")

    # Trending by downloads
    trending = catalog.trending(limit=3)
    print("\n  Top 3 by downloads (trending):")
    for rank, agent in enumerate(trending, start=1):
        print(f"    #{rank}  [{agent.agent_id}] {agent.name} — {agent.downloads:,} downloads")

    print()


# ---------------------------------------------------------------------------
# Demo 5: Assemble an agent pipeline by capability
# ---------------------------------------------------------------------------


def demo_pipeline_assembly(catalog: AgentCatalog) -> None:
    """Show how to find the best agent for each step in a multi-agent pipeline."""
    print("=" * 60)
    print("DEMO 5: Assemble a Multi-Agent Pipeline by Capability")
    print("=" * 60)

    pipeline_steps: list[tuple[str, str]] = [
        ("web_scraping", "Step 1 — Web Scraper"),
        ("structured_output", "Step 2 — Structured Output"),
        ("document_summarization", "Step 3 — Summarizer"),
    ]

    print("  Building pipeline — selecting best-rated agent per capability:")
    for capability, step_name in pipeline_steps:
        results = catalog.search(SearchFilter(
            capabilities=[capability],
            min_rating=4.0,
        ))
        if results:
            best = results[0]  # sorted by rating desc
            print(f"\n  {step_name}")
            print(f"    Agent:   {best.name} (rating: {best.rating}/5.0)")
            print(f"    Install: {best.install_command}")
        else:
            print(f"\n  {step_name}")
            print(f"    No agent with capability '{capability}' and rating >= 4.0 found.")

    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all quickstart demos."""
    print("\naumai-agentmarket Quickstart Examples")
    print("Version:", end=" ")
    import aumai_agentmarket
    print(aumai_agentmarket.__version__)
    print()

    catalog = build_sample_catalog()
    print(f"  Sample catalog populated with {len(list(catalog._listings.values()))} agents.")
    print()

    demo_publish_and_retrieve(catalog)
    demo_search(catalog)
    demo_reviews_and_ratings(catalog)
    demo_leaderboards(catalog)
    demo_pipeline_assembly(catalog)

    print("All demos completed successfully.")


if __name__ == "__main__":
    main()
