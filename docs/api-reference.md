# API Reference — aumai-agentmarket

Complete reference for all public classes, functions, and Pydantic models.

---

## Module: `aumai_agentmarket.core`

### `AgentNotFoundError`

```python
class AgentNotFoundError(KeyError)
```

Raised when an `agent_id` is not present in the catalog. Inherits from `KeyError` so it can be caught with either `AgentNotFoundError` or `KeyError`.

**Example:**

```python
from aumai_agentmarket import AgentCatalog, AgentNotFoundError

catalog = AgentCatalog()
try:
    catalog.get("nonexistent-agent")
except AgentNotFoundError as exc:
    print(str(exc))  # "Agent 'nonexistent-agent' not found."
```

---

### `AgentCatalog`

```python
class AgentCatalog
```

In-memory catalog of agent marketplace listings with integrated review management and rating computation.

Maintains two internal data structures: `_listings: dict[str, AgentListing]` keyed by `agent_id`, and `_reviews: dict[str, list[AgentReview]]` as a `defaultdict(list)`.

**Constructor:**

```python
AgentCatalog() -> None
```

Initializes an empty catalog with no listings and no reviews.

---

#### `AgentCatalog.register`

```python
def register(self, listing: AgentListing) -> None
```

Add or overwrite an agent listing.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `listing` | `AgentListing` | The agent listing to register. `agent_id` is the key. |

**Returns:** `None`

**Notes:** If a listing with the same `agent_id` already exists, it is silently replaced. Reviews for that `agent_id` are not cleared — they remain in `_reviews`.

**Example:**

```python
from aumai_agentmarket import AgentCatalog, AgentListing

catalog = AgentCatalog()
catalog.register(AgentListing(
    agent_id="web-scraper-v1",
    name="Web Scraper Agent",
    description="Scrapes and parses web pages into structured JSON.",
    author="AumAI Web Team",
    capabilities=["web_scraping", "html_parsing", "structured_output"],
    license="Apache-2.0",
    install_command="pip install aumai-agent-web-scraper",
))
```

---

#### `AgentCatalog.search`

```python
def search(self, search_filter: SearchFilter) -> list[AgentListing]
```

Search listings according to the provided filter. Returns results sorted by rating descending.

All non-`None` filter fields must match for a listing to be included.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `search_filter` | `SearchFilter` | Search parameters. See `SearchFilter` model documentation. |

**Returns:** `list[AgentListing]` — matching listings sorted by `rating` descending.

**Filter evaluation order:**
1. `query` — case-insensitive substring match on `name` OR `description`
2. `capabilities` — every requested capability must appear in `listing.capabilities`
3. `min_rating` — `listing.rating >= search_filter.min_rating`
4. `tags` — every requested tag must appear in `listing.tags`

**Example:**

```python
from aumai_agentmarket import SearchFilter

results = catalog.search(SearchFilter(
    query="document",
    capabilities=["pdf_parsing", "structured_output"],
    min_rating=4.0,
    tags=["finance"],
))
for listing in results:
    print(listing.agent_id, listing.rating)
```

---

#### `AgentCatalog.get`

```python
def get(self, agent_id: str) -> AgentListing
```

Return the listing for the given agent ID.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `agent_id` | `str` | Unique identifier of the agent. Case-sensitive. |

**Returns:** `AgentListing`

**Raises:** `AgentNotFoundError` — if no listing with that ID exists.

**Example:**

```python
listing = catalog.get("web-scraper-v1")
print(listing.name, listing.rating, listing.install_command)
```

---

#### `AgentCatalog.add_review`

```python
def add_review(self, agent_id: str, review: AgentReview) -> None
```

Add a review to an agent and recompute its mean rating.

The new rating is computed as the arithmetic mean of all reviews for that agent, rounded to 2 decimal places. The listing's `rating` field is updated in place using `model_copy(update=...)`.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `agent_id` | `str` | The agent being reviewed. Must exist in the catalog. |
| `review` | `AgentReview` | The review to attach. |

**Returns:** `None`

**Raises:** `AgentNotFoundError` — if the agent does not exist.

**Example:**

```python
from aumai_agentmarket import AgentReview

catalog.add_review("web-scraper-v1", AgentReview(
    reviewer="alice",
    rating=4.5,
    comment="Handles JavaScript-rendered pages well.",
))
catalog.add_review("web-scraper-v1", AgentReview(
    reviewer="bob",
    rating=3.5,
    comment="Slow on large sitemaps.",
))

updated = catalog.get("web-scraper-v1")
print(updated.rating)  # 4.0 (mean of 4.5 and 3.5)
```

---

#### `AgentCatalog.top_rated`

```python
def top_rated(self, limit: int = 10) -> list[AgentListing]
```

Return the highest-rated agents across the entire catalog.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `10` | Maximum number of results. |

**Returns:** `list[AgentListing]` — sorted by `rating` descending.

**Example:**

```python
top_5 = catalog.top_rated(limit=5)
for agent in top_5:
    print(f"{agent.name}: {agent.rating:.2f}/5.0")
```

---

#### `AgentCatalog.trending`

```python
def trending(self, limit: int = 10) -> list[AgentListing]
```

Return trending agents sorted by total download count descending. Uses `downloads` as a proxy for recency since per-period download timestamps are not tracked in `AgentListing`.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `10` | Maximum number of results. |

**Returns:** `list[AgentListing]` — sorted by `downloads` descending.

**Example:**

```python
trending = catalog.trending(limit=10)
for agent in trending:
    print(f"{agent.name}: {agent.downloads:,} downloads")
```

---

#### `AgentCatalog.get_reviews`

```python
def get_reviews(self, agent_id: str) -> list[AgentReview]
```

Return all reviews for an agent, in the order they were added.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `agent_id` | `str` | The agent whose reviews are requested. |

**Returns:** `list[AgentReview]` — empty list if no reviews have been added. Does **not** raise `AgentNotFoundError` for unregistered agents.

**Example:**

```python
reviews = catalog.get_reviews("web-scraper-v1")
for review in reviews:
    print(f"{review.reviewer}: {review.rating}/5  {review.comment}")
```

---

## Module: `aumai_agentmarket.models`

### `AgentListing`

```python
class AgentListing(BaseModel)
```

A marketplace listing for a pre-built agent. Represents the published artifact that consumers discover and install.

**Fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `agent_id` | `str` | Yes | — | Unique identifier. Used as the catalog key. |
| `name` | `str` | Yes | — | Human-readable agent name. |
| `description` | `str` | Yes | — | What the agent does. |
| `version` | `str` | No | `"1.0.0"` | Semantic version string. |
| `author` | `str` | Yes | — | Author or organisation name. |
| `capabilities` | `list[str]` | No | `[]` | Functional capabilities the agent provides. Used for capability-based search. |
| `tags` | `list[str]` | No | `[]` | Free-form search tags. |
| `downloads` | `int` | No | `0` | Total download count. Must be `>= 0`. |
| `rating` | `float` | No | `0.0` | Mean star rating. Must be in `[0.0, 5.0]`. |
| `license` | `str` | Yes | — | SPDX license identifier (e.g. `"Apache-2.0"`). |
| `install_command` | `str` | Yes | — | Shell command to install the agent (e.g. `"pip install my-agent"`). |
| `created_at` | `datetime` | No | `datetime.now(UTC)` | UTC timestamp of listing creation. |

**Example:**

```python
from aumai_agentmarket.models import AgentListing

listing = AgentListing(
    agent_id="sql-agent-v3",
    name="SQL Query Agent",
    description="Translates natural language questions to optimized SQL queries.",
    version="3.1.2",
    author="AumAI Data Team",
    capabilities=["text_to_sql", "schema_introspection", "query_optimization"],
    tags=["sql", "database", "analytics"],
    downloads=4200,
    rating=4.7,
    license="Apache-2.0",
    install_command="pip install aumai-agent-sql",
)

# Round-trip serialization
record = listing.model_dump(mode="json")
restored = AgentListing.model_validate(record)
```

---

### `AgentReview`

```python
class AgentReview(BaseModel)
```

A user review for an agent listing. Reviews are attached via `AgentCatalog.add_review()`.

**Fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `reviewer` | `str` | Yes | — | Username or display name of the reviewer. |
| `rating` | `float` | Yes | — | Star rating. Must be in `[0.0, 5.0]`. |
| `comment` | `str` | No | `""` | Optional review text. |
| `created_at` | `datetime` | No | `datetime.now(UTC)` | UTC timestamp of the review. |

**Example:**

```python
from aumai_agentmarket.models import AgentReview

review = AgentReview(
    reviewer="dev_alice",
    rating=4.8,
    comment="Generates correct SQL 95% of the time. Excellent for analytics use cases.",
)
print(review.rating)   # 4.8
print(review.comment)  # "Generates correct SQL..."
```

---

### `SearchFilter`

```python
class SearchFilter(BaseModel)
```

Filter parameters for agent catalog search. All fields are optional. Only non-`None` fields are applied as active filters.

**Fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | `str \| None` | No | `None` | Substring to match in `name` OR `description` (case-insensitive). |
| `capabilities` | `list[str] \| None` | No | `None` | Required capabilities. **All** must be present in the listing. |
| `min_rating` | `float \| None` | No | `None` | Minimum acceptable rating. Must be in `[0.0, 5.0]`. |
| `tags` | `list[str] \| None` | No | `None` | Required tags. **All** must be present in the listing. |

**Validators:**

`min_rating` is validated by a `@field_validator` that enforces the range `[0.0, 5.0]`, raising `ValueError: min_rating must be between 0.0 and 5.0.` for out-of-range values.

**Example:**

```python
from aumai_agentmarket.models import SearchFilter

# Match everything (no active filters)
all_agents = SearchFilter()

# Text search only
by_text = SearchFilter(query="invoice")

# Capability and quality gate
quality_gate = SearchFilter(
    capabilities=["ocr", "structured_output"],
    min_rating=4.2,
)

# Full filter
precise = SearchFilter(
    query="finance",
    capabilities=["pdf_parsing"],
    min_rating=4.5,
    tags=["enterprise", "production-ready"],
)
```

---

## Module: `aumai_agentmarket.cli`

The CLI is a Click group registered as the `aumai-agentmarket` entry point. All commands share a module-level `AgentCatalog` singleton — state persists only within a single process invocation.

### Commands summary

| Command | Description |
|---|---|
| `search [--query TEXT] [--min-rating FLOAT] [--capability TEXT ...] [--tag TEXT ...]` | Search the agent catalog |
| `publish --config PATH` | Publish an agent from a JSON manifest file |
| `serve [--host TEXT] [--port INT]` | Start the FastAPI marketplace HTTP server |
| `top-rated [--limit N]` | Show highest-rated agents |
| `get AGENT_ID` | Show full JSON details for an agent by ID |

---

## Package exports (`aumai_agentmarket.__init__`)

The following names are importable directly from `aumai_agentmarket`:

```python
from aumai_agentmarket import (
    AgentCatalog,
    AgentListing,
    AgentNotFoundError,
    AgentReview,
    SearchFilter,
)
```

Package version:

```python
import aumai_agentmarket
print(aumai_agentmarket.__version__)  # "0.1.0"
```
