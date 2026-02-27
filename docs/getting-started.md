# Getting Started with aumai-agentmarket

This guide walks you from installation to a running agent marketplace — publishing agents, searching the catalog, writing reviews, and querying leaderboards — in under 15 minutes.

---

## Prerequisites

- Python 3.11 or later
- pip (or your preferred package manager)
- Optional: `uvicorn` for the HTTP server mode (`pip install uvicorn`)

No database or cloud account is required. Everything runs locally in-memory by default.

---

## Installation

### From PyPI (recommended)

```bash
pip install aumai-agentmarket
```

### With the HTTP server dependency

```bash
pip install "aumai-agentmarket[server]"
# or manually: pip install aumai-agentmarket uvicorn
```

### From source

```bash
git clone https://github.com/aumai/aumai-agentmarket.git
cd aumai-agentmarket
pip install -e ".[dev]"
```

### Verify

```bash
aumai-agentmarket --version
python -c "import aumai_agentmarket; print(aumai_agentmarket.__version__)"
```

---

## Core Concepts

**AgentListing** is the published artifact. It carries everything needed to evaluate and install an agent: a unique `agent_id`, human-readable `name` and `description`, `version`, `author`, a list of `capabilities` (what the agent can do), `tags` (search labels), `downloads`, the current `rating`, `license`, and the `install_command` to deploy it.

**AgentCatalog** is the registry. It stores listings in memory, manages the review-to-rating pipeline, and exposes search, leaderboard, and trending queries.

**SearchFilter** is the query object. All fields are optional. You combine whichever filters you need — text query, required capabilities, minimum rating, required tags — and pass the `SearchFilter` to `catalog.search()`.

**AgentReview** is the feedback record. Each review has a `reviewer` identifier, a `rating` (0–5), and an optional `comment`. Adding a review automatically recomputes the agent's mean rating.

---

## Step-by-Step Tutorial

### Step 1: Create your first agent manifest

Create `my-agent.json`:

```json
{
  "agent_id": "summarizer-agent-v1",
  "name": "Document Summarizer Agent",
  "description": "Summarizes long documents into structured executive briefings with key points, risks, and recommendations.",
  "version": "1.0.0",
  "author": "AumAI Research",
  "capabilities": ["document_summarization", "structured_output", "risk_extraction"],
  "tags": ["nlp", "summarization", "enterprise"],
  "downloads": 0,
  "rating": 0.0,
  "license": "Apache-2.0",
  "install_command": "pip install aumai-agent-summarizer"
}
```

### Step 2: Publish the agent

```bash
aumai-agentmarket publish --config my-agent.json
# Agent 'summarizer-agent-v1' published successfully.
```

### Step 3: Search for agents

```bash
# Search by keyword
aumai-agentmarket search --query "summarization"

# Filter by capability
aumai-agentmarket search --capability document_summarization

# Filter by capability and minimum rating
aumai-agentmarket search --capability structured_output --min-rating 4.0
```

### Step 4: Get full details

```bash
aumai-agentmarket get summarizer-agent-v1
```

Output is a JSON object with all `AgentListing` fields.

### Step 5: Browse the leaderboard

```bash
# Top 5 by rating
aumai-agentmarket top-rated --limit 5
```

### Step 6: Start the marketplace server (optional)

```bash
aumai-agentmarket serve --host 0.0.0.0 --port 8000
# Starting Agent Marketplace server on 0.0.0.0:8000 ...
```

The server exposes the catalog over HTTP. Other services and CI pipelines can now query it via REST.

---

## Common Patterns

### Pattern 1: Publish and immediately search

```python
from aumai_agentmarket import AgentCatalog, AgentListing, SearchFilter

catalog = AgentCatalog()

catalog.register(AgentListing(
    agent_id="data-extractor-v1",
    name="Structured Data Extractor",
    description="Extracts entities, tables, and key-value pairs from unstructured text.",
    version="1.0.0",
    author="AumAI Data Team",
    capabilities=["entity_extraction", "table_parsing", "structured_output"],
    tags=["nlp", "extraction", "data"],
    license="Apache-2.0",
    install_command="pip install aumai-agent-data-extractor",
))

# Immediately searchable
results = catalog.search(SearchFilter(capabilities=["entity_extraction"]))
print(results[0].name)  # Structured Data Extractor
```

### Pattern 2: Build a review pipeline

Collect reviews from users and watch ratings update in real time:

```python
from aumai_agentmarket import AgentReview

reviews = [
    AgentReview(reviewer="user_001", rating=4.9, comment="Best extraction agent I have used."),
    AgentReview(reviewer="user_002", rating=4.5, comment="Very accurate on financial tables."),
    AgentReview(reviewer="user_003", rating=3.8, comment="Struggles with nested lists."),
]

for review in reviews:
    catalog.add_review("data-extractor-v1", review)

listing = catalog.get("data-extractor-v1")
print(f"Updated rating: {listing.rating}")  # mean of 4.9, 4.5, 3.8 = 4.4
```

### Pattern 3: Multi-criteria search with all filter types

```python
from aumai_agentmarket import SearchFilter

results = catalog.search(SearchFilter(
    query="extraction",                              # text match
    capabilities=["structured_output", "ocr"],      # all must be present
    min_rating=4.0,                                 # rating gate
    tags=["finance"],                               # all must be present
))
```

### Pattern 4: Curate a capability-based team of agents

Select agents for a multi-step pipeline by querying each required capability:

```python
def find_best_agent(
    catalog: AgentCatalog,
    required_capability: str,
    min_rating: float = 4.0,
) -> AgentListing | None:
    results = catalog.search(SearchFilter(
        capabilities=[required_capability],
        min_rating=min_rating,
    ))
    return results[0] if results else None

reader = find_best_agent(catalog, "pdf_parsing")
extractor = find_best_agent(catalog, "entity_extraction")
summarizer = find_best_agent(catalog, "document_summarization")

if all([reader, extractor, summarizer]):
    print("Pipeline ready:")
    for agent in [reader, extractor, summarizer]:
        print(f"  {agent.name}: {agent.install_command}")
```

### Pattern 5: Persist and restore the catalog

```python
import json
from aumai_agentmarket import AgentCatalog, AgentListing

def save(catalog: AgentCatalog, path: str) -> None:
    listings = list(catalog._listings.values())
    data = [item.model_dump(mode="json") for item in listings]
    with open(path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2, default=str)

def load(path: str) -> AgentCatalog:
    catalog = AgentCatalog()
    try:
        with open(path, encoding="utf-8") as file_handle:
            records = json.load(file_handle)
        for rec in records:
            catalog.register(AgentListing.model_validate(rec))
    except FileNotFoundError:
        pass
    return catalog
```

---

## Troubleshooting FAQ

**Q: `aumai-agentmarket` command not found after pip install.**

Make sure your Python scripts directory is on your `PATH`. With virtual environments this is automatic. Try `python -m aumai_agentmarket.cli --help` as a fallback.

---

**Q: `AgentNotFoundError: Agent 'my-id' not found.`**

The catalog is in-memory. State does not survive process restarts unless you persist and reload. See Pattern 5.

---

**Q: Publish fails with a Pydantic validation error.**

Check the JSON manifest carefully. Required fields with no defaults are `agent_id`, `name`, `description`, `author`, `license`, and `install_command`. The `rating` field must be in `[0.0, 5.0]` and `downloads` must be `>= 0`. The error message will name the exact offending field.

---

**Q: `SearchFilter` raises a `ValueError` for `min_rating`.**

`min_rating` must be between 0.0 and 5.0 inclusive. A value of `6.0` or `-1.0` will raise `ValueError: min_rating must be between 0.0 and 5.0.`

---

**Q: `add_review` raises `AgentNotFoundError` even though I just registered the agent.**

`add_review` calls `catalog.get(agent_id)` internally. Confirm you are using the exact same `agent_id` string (case-sensitive) that you used when registering.

---

**Q: The `serve` command fails with `ModuleNotFoundError: No module named 'uvicorn'`.**

Install uvicorn: `pip install uvicorn`. The dependency is optional and not bundled with the base package.

---

**Q: Search returns no results even though I registered agents.**

Remember: every non-`None` field in `SearchFilter` is a strict filter — it must match for the listing to be included. For capability and tag filters, *all* requested values must be present. Try a minimal `SearchFilter(query="")` to check that agents are registered, then add filters one at a time to diagnose which filter eliminates the result.

---

## Next Steps

- [API Reference](api-reference.md) — complete documentation of every class, method, and model field
- [Examples](../examples/quickstart.py) — runnable quickstart script
- [Contributing](../CONTRIBUTING.md) — how to submit improvements
- [Discord community](https://discord.gg/aumai) — questions and discussion
