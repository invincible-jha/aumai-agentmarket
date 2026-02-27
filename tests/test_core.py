"""Tests for aumai-agentmarket core module."""

from __future__ import annotations

import pytest

from aumai_agentmarket.core import AgentCatalog, AgentNotFoundError
from aumai_agentmarket.models import AgentListing, AgentReview, SearchFilter


# ---------------------------------------------------------------------------
# AgentListing model tests
# ---------------------------------------------------------------------------


class TestAgentListingModel:
    def test_valid_creation(self, code_review_agent: AgentListing) -> None:
        assert code_review_agent.agent_id == "code-review-v1"
        assert code_review_agent.rating == 4.2
        assert code_review_agent.downloads == 1500

    def test_default_rating_zero(self) -> None:
        agent = AgentListing(
            agent_id="new-agent",
            name="New",
            description="desc",
            author="Author",
            license="MIT",
            install_command="pip install x",
        )
        assert agent.rating == 0.0

    def test_default_downloads_zero(self) -> None:
        agent = AgentListing(
            agent_id="new-agent",
            name="New",
            description="desc",
            author="Author",
            license="MIT",
            install_command="pip install x",
        )
        assert agent.downloads == 0

    def test_rating_above_five_raises(self) -> None:
        with pytest.raises(Exception):
            AgentListing(
                agent_id="bad",
                name="Bad",
                description="bad",
                author="X",
                license="MIT",
                install_command="x",
                rating=5.1,
            )

    def test_negative_downloads_raises(self) -> None:
        with pytest.raises(Exception):
            AgentListing(
                agent_id="bad",
                name="Bad",
                description="bad",
                author="X",
                license="MIT",
                install_command="x",
                downloads=-1,
            )


# ---------------------------------------------------------------------------
# SearchFilter model tests
# ---------------------------------------------------------------------------


class TestSearchFilterModel:
    def test_all_none_filter(self) -> None:
        sf = SearchFilter()
        assert sf.query is None
        assert sf.capabilities is None
        assert sf.min_rating is None
        assert sf.tags is None

    def test_min_rating_validation_valid(self) -> None:
        sf = SearchFilter(min_rating=3.5)
        assert sf.min_rating == 3.5

    def test_min_rating_validation_boundary(self) -> None:
        sf = SearchFilter(min_rating=0.0)
        assert sf.min_rating == 0.0
        sf2 = SearchFilter(min_rating=5.0)
        assert sf2.min_rating == 5.0

    def test_min_rating_out_of_range_raises(self) -> None:
        with pytest.raises(Exception):
            SearchFilter(min_rating=5.1)

    def test_min_rating_negative_raises(self) -> None:
        with pytest.raises(Exception):
            SearchFilter(min_rating=-0.1)


# ---------------------------------------------------------------------------
# AgentCatalog tests
# ---------------------------------------------------------------------------


class TestAgentCatalog:
    def test_register_and_get(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        result = catalog.get("code-review-v1")
        assert result.agent_id == "code-review-v1"

    def test_register_overwrites(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        updated = code_review_agent.model_copy(update={"name": "Updated Agent"})
        catalog.register(updated)
        assert catalog.get("code-review-v1").name == "Updated Agent"

    def test_get_missing_raises(self) -> None:
        catalog = AgentCatalog()
        with pytest.raises(AgentNotFoundError):
            catalog.get("nonexistent-agent")

    def test_get_missing_error_message(self) -> None:
        catalog = AgentCatalog()
        with pytest.raises(AgentNotFoundError, match="nonexistent"):
            catalog.get("nonexistent")

    def test_search_by_query_name(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        results = catalog.search(SearchFilter(query="code review"))
        assert len(results) == 1
        assert results[0].agent_id == "code-review-v1"

    def test_search_case_insensitive(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        results = catalog.search(SearchFilter(query="CODE REVIEW"))
        assert len(results) == 1

    def test_search_by_description(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        results = catalog.search(SearchFilter(query="AI-powered"))
        assert len(results) == 1

    def test_search_no_match(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        results = catalog.search(SearchFilter(query="zzznomatch"))
        assert results == []

    def test_search_filter_by_capability(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        catalog.register(doc_agent)
        results = catalog.search(SearchFilter(capabilities=["code-review"]))
        assert all("code-review" in r.capabilities for r in results)
        assert len(results) == 1

    def test_search_all_capabilities_must_match(
        self, code_review_agent: AgentListing
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        # code-review-v1 has ["code-review", "linting", "suggestions"]
        results = catalog.search(
            SearchFilter(capabilities=["code-review", "linting"])
        )
        assert len(results) == 1
        results2 = catalog.search(
            SearchFilter(capabilities=["code-review", "documentation"])
        )
        assert results2 == []

    def test_search_filter_by_min_rating(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)  # rating 4.2
        catalog.register(doc_agent)  # rating 3.8
        results = catalog.search(SearchFilter(min_rating=4.0))
        assert all(r.rating >= 4.0 for r in results)
        assert len(results) == 1

    def test_search_filter_by_tags(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        catalog.register(doc_agent)
        results = catalog.search(SearchFilter(tags=["docs"]))
        assert len(results) == 1
        assert results[0].agent_id == "doc-writer-v1"

    def test_search_sorted_by_rating_desc(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)  # 4.2
        catalog.register(doc_agent)  # 3.8
        results = catalog.search(SearchFilter())
        # Should be sorted rating desc
        for i in range(len(results) - 1):
            assert results[i].rating >= results[i + 1].rating

    def test_search_empty_filter_returns_all(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        catalog.register(doc_agent)
        results = catalog.search(SearchFilter())
        assert len(results) == 2

    def test_add_review_updates_rating(
        self,
        code_review_agent: AgentListing,
        agent_review: AgentReview,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)  # initial rating 4.2
        catalog.add_review("code-review-v1", agent_review)  # review rating 5.0
        updated = catalog.get("code-review-v1")
        # New rating = mean(4.2, 5.0) is not right — reviews start fresh.
        # The first add_review uses only the reviews list, so new rating = 5.0
        assert updated.rating == 5.0

    def test_add_review_multiple_averages(
        self, code_review_agent: AgentListing
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        r1 = AgentReview(reviewer="u1", rating=4.0)
        r2 = AgentReview(reviewer="u2", rating=2.0)
        catalog.add_review("code-review-v1", r1)
        catalog.add_review("code-review-v1", r2)
        updated = catalog.get("code-review-v1")
        assert updated.rating == round((4.0 + 2.0) / 2, 2)

    def test_add_review_missing_agent_raises(
        self, agent_review: AgentReview
    ) -> None:
        catalog = AgentCatalog()
        with pytest.raises(AgentNotFoundError):
            catalog.add_review("nonexistent", agent_review)

    def test_get_reviews_empty(self, code_review_agent: AgentListing) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        reviews = catalog.get_reviews("code-review-v1")
        assert reviews == []

    def test_get_reviews_after_add(
        self,
        code_review_agent: AgentListing,
        agent_review: AgentReview,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        catalog.add_review("code-review-v1", agent_review)
        reviews = catalog.get_reviews("code-review-v1")
        assert len(reviews) == 1
        assert reviews[0].reviewer == "test-user"

    def test_top_rated_empty(self) -> None:
        catalog = AgentCatalog()
        assert catalog.top_rated() == []

    def test_top_rated_returns_sorted(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)  # 4.2
        catalog.register(doc_agent)  # 3.8
        results = catalog.top_rated(limit=10)
        assert results[0].agent_id == "code-review-v1"
        assert results[1].agent_id == "doc-writer-v1"

    def test_top_rated_limit(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        catalog.register(doc_agent)
        results = catalog.top_rated(limit=1)
        assert len(results) == 1

    def test_trending_empty(self) -> None:
        catalog = AgentCatalog()
        assert catalog.trending() == []

    def test_trending_sorted_by_downloads(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)  # 1500 downloads
        catalog.register(doc_agent)  # 800 downloads
        results = catalog.trending(limit=10)
        assert results[0].downloads >= results[1].downloads

    def test_trending_limit(
        self,
        code_review_agent: AgentListing,
        doc_agent: AgentListing,
    ) -> None:
        catalog = AgentCatalog()
        catalog.register(code_review_agent)
        catalog.register(doc_agent)
        results = catalog.trending(limit=1)
        assert len(results) == 1
