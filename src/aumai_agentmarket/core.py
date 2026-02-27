"""Core logic for aumai-agentmarket."""

from __future__ import annotations

from collections import defaultdict

from aumai_agentmarket.models import AgentListing, AgentReview, SearchFilter


class AgentNotFoundError(KeyError):
    """Raised when an agent_id is not present in the catalog."""


class AgentCatalog:
    """In-memory catalog of agent marketplace listings with reviews."""

    def __init__(self) -> None:
        self._listings: dict[str, AgentListing] = {}
        self._reviews: dict[str, list[AgentReview]] = defaultdict(list)

    def register(self, listing: AgentListing) -> None:
        """Add or overwrite an agent listing.

        Args:
            listing: The agent listing to register.
        """
        self._listings[listing.agent_id] = listing

    def search(self, search_filter: SearchFilter) -> list[AgentListing]:
        """Search listings according to the provided filter.

        All non-None filter fields must match for a listing to be included.

        Args:
            search_filter: Search parameters.

        Returns:
            Matching agent listings sorted by rating descending.
        """
        results: list[AgentListing] = []

        for listing in self._listings.values():
            if search_filter.query is not None:
                query_lower = search_filter.query.lower()
                text_match = (
                    query_lower in listing.name.lower()
                    or query_lower in listing.description.lower()
                )
                if not text_match:
                    continue

            if search_filter.capabilities is not None:
                listing_caps = set(listing.capabilities)
                if not all(cap in listing_caps for cap in search_filter.capabilities):
                    continue

            if search_filter.min_rating is not None and listing.rating < search_filter.min_rating:
                continue

            if search_filter.tags is not None:
                listing_tags = set(listing.tags)
                if not all(tag in listing_tags for tag in search_filter.tags):
                    continue

            results.append(listing)

        results.sort(key=lambda item: item.rating, reverse=True)
        return results

    def get(self, agent_id: str) -> AgentListing:
        """Return the listing for the given agent ID.

        Args:
            agent_id: Unique identifier of the agent.

        Returns:
            The matching ``AgentListing``.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        try:
            return self._listings[agent_id]
        except KeyError:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found.") from None

    def add_review(self, agent_id: str, review: AgentReview) -> None:
        """Add a review to an agent and recompute its mean rating.

        Args:
            agent_id: The agent being reviewed.
            review: The review to attach.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        listing = self.get(agent_id)
        self._reviews[agent_id].append(review)

        all_reviews = self._reviews[agent_id]
        new_rating = sum(r.rating for r in all_reviews) / len(all_reviews)

        updated = listing.model_copy(update={"rating": round(new_rating, 2)})
        self._listings[agent_id] = updated

    def top_rated(self, limit: int = 10) -> list[AgentListing]:
        """Return the highest-rated agents.

        Args:
            limit: Maximum number of results.

        Returns:
            Agent listings sorted by rating descending.
        """
        sorted_listings = sorted(
            self._listings.values(), key=lambda item: item.rating, reverse=True
        )
        return sorted_listings[:limit]

    def trending(self, limit: int = 10) -> list[AgentListing]:
        """Return trending agents sorted by recent download count.

        Currently uses total ``downloads`` as a proxy for recency, since
        download timestamps are not tracked in ``AgentListing``.

        Args:
            limit: Maximum number of results.

        Returns:
            Agent listings sorted by downloads descending.
        """
        sorted_listings = sorted(
            self._listings.values(), key=lambda item: item.downloads, reverse=True
        )
        return sorted_listings[:limit]

    def get_reviews(self, agent_id: str) -> list[AgentReview]:
        """Return all reviews for an agent.

        Args:
            agent_id: The agent whose reviews are requested.

        Returns:
            List of ``AgentReview`` objects.
        """
        return list(self._reviews[agent_id])


__all__ = [
    "AgentCatalog",
    "AgentNotFoundError",
]
