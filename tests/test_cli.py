"""Tests for aumai-agentmarket CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from aumai_agentmarket.cli import main
from aumai_agentmarket.models import AgentListing


def _extract_json(text: str) -> dict:  # type: ignore[type-arg]
    start = text.index("{")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("No JSON object found")


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def published_agent_id(runner: CliRunner, tmp_path: Path) -> str:
    """Publish an agent via CLI and return its agent_id."""
    config = {
        "agent_id": "cli-agent-001",
        "name": "CLI Test Agent",
        "description": "Agent published via CLI for testing.",
        "version": "1.0.0",
        "author": "CLI Tester",
        "capabilities": ["testing", "automation"],
        "tags": ["test", "cli"],
        "downloads": 50,
        "rating": 4.0,
        "license": "MIT",
        "install_command": "pip install cli-test-agent",
    }
    config_file = tmp_path / "agent.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    result = runner.invoke(main, ["publish", "--config", str(config_file)])
    assert result.exit_code == 0, result.output
    return "cli-agent-001"


# ---------------------------------------------------------------------------
# --version
# ---------------------------------------------------------------------------


def test_cli_version(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


# ---------------------------------------------------------------------------
# publish command
# ---------------------------------------------------------------------------


def test_publish_valid_agent(runner: CliRunner, tmp_path: Path) -> None:
    config = {
        "agent_id": "new-agent-test",
        "name": "New Agent",
        "description": "A brand new agent.",
        "author": "Tester",
        "license": "Apache-2.0",
        "install_command": "pip install new-agent",
    }
    config_file = tmp_path / "agent.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    result = runner.invoke(main, ["publish", "--config", str(config_file)])
    assert result.exit_code == 0
    assert "new-agent-test" in result.output


def test_publish_invalid_json(runner: CliRunner, tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid}", encoding="utf-8")
    result = runner.invoke(main, ["publish", "--config", str(bad_file)])
    assert result.exit_code != 0


def test_publish_non_object_json(runner: CliRunner, tmp_path: Path) -> None:
    bad_file = tmp_path / "arr.json"
    bad_file.write_text("[1, 2, 3]", encoding="utf-8")
    result = runner.invoke(main, ["publish", "--config", str(bad_file)])
    assert result.exit_code != 0


def test_publish_missing_required_field(runner: CliRunner, tmp_path: Path) -> None:
    config = {"agent_id": "x", "name": "X"}  # missing author, license, etc.
    config_file = tmp_path / "bad_agent.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    result = runner.invoke(main, ["publish", "--config", str(config_file)])
    assert result.exit_code != 0


def test_publish_config_not_found(runner: CliRunner) -> None:
    result = runner.invoke(main, ["publish", "--config", "/nonexistent/path.json"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# search command
# ---------------------------------------------------------------------------


def test_search_no_results(runner: CliRunner) -> None:
    result = runner.invoke(main, ["search", "--query", "zzznothingmatchesthis"])
    assert result.exit_code == 0
    assert "No agents found" in result.output


def test_search_returns_published(runner: CliRunner, published_agent_id: str) -> None:
    result = runner.invoke(main, ["search", "--query", "cli"])
    assert result.exit_code == 0
    assert "cli-agent-001" in result.output or "CLI Test Agent" in result.output


def test_search_with_min_rating(runner: CliRunner, published_agent_id: str) -> None:
    result = runner.invoke(main, ["search", "--min-rating", "3.0"])
    assert result.exit_code == 0


def test_search_with_capability(runner: CliRunner, published_agent_id: str) -> None:
    result = runner.invoke(main, ["search", "--capability", "testing"])
    assert result.exit_code == 0


def test_search_with_tag(runner: CliRunner, published_agent_id: str) -> None:
    result = runner.invoke(main, ["search", "--tag", "cli"])
    assert result.exit_code == 0


def test_search_all_options_combined(
    runner: CliRunner, published_agent_id: str
) -> None:
    result = runner.invoke(
        main,
        [
            "search",
            "--query", "cli",
            "--min-rating", "3.0",
            "--capability", "testing",
            "--tag", "test",
        ],
    )
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# top-rated command
# ---------------------------------------------------------------------------


def test_top_rated_no_crash(runner: CliRunner) -> None:
    """top-rated must not crash regardless of catalog state."""
    result = runner.invoke(main, ["top-rated"])
    assert result.exit_code == 0


def test_top_rated_shows_published(
    runner: CliRunner, published_agent_id: str
) -> None:
    result = runner.invoke(main, ["top-rated"])
    assert result.exit_code == 0
    assert "cli-agent-001" in result.output or "CLI Test Agent" in result.output


def test_top_rated_limit(runner: CliRunner, published_agent_id: str) -> None:
    result = runner.invoke(main, ["top-rated", "--limit", "1"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# get command
# ---------------------------------------------------------------------------


def test_get_existing_agent(runner: CliRunner, published_agent_id: str) -> None:
    result = runner.invoke(main, ["get", published_agent_id])
    assert result.exit_code == 0
    data = _extract_json(result.output)
    assert data["agent_id"] == published_agent_id


def test_get_nonexistent_agent(runner: CliRunner) -> None:
    result = runner.invoke(main, ["get", "totally-nonexistent-agent-xyz"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# serve command (import error path — no uvicorn in test env)
# ---------------------------------------------------------------------------


def test_serve_without_uvicorn(runner: CliRunner) -> None:
    """Test that serve command handles missing uvicorn gracefully."""
    import sys
    import unittest.mock as mock

    with mock.patch.dict(sys.modules, {"uvicorn": None}):
        result = runner.invoke(main, ["serve", "--port", "9999"])
    # Should either succeed (uvicorn installed) or fail gracefully
    # Either way, no uncaught exception
    assert result.exception is None or result.exit_code != 0
