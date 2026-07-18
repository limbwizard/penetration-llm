from __future__ import annotations

from pentest_llm.methodology import (
    PHASE_GUIDES,
    format_methodology,
    matching_guides,
    tool_inventory,
)
from pentest_llm.models import Scope


def test_matching_guides_filters_by_allowed_categories():
    scope = Scope(allowed_categories=["recon"])
    names = {g.name for g in matching_guides(scope)}
    assert "recon" in names
    # reporting is always included; scanning-only categories are filtered out.
    assert "reporting" in names
    assert "scanning" not in names


def test_matching_guides_specific_phase():
    scope = Scope(allowed_categories=["recon", "scanning"])
    guides = matching_guides(scope, "scanning")
    assert [g.name for g in guides] == ["scanning"]


def test_matching_guides_all_returns_every_allowed_phase():
    # Categories are matched against each guide's `categories`, not its name, so
    # cover one category per guide; reporting is always included regardless.
    scope = Scope(
        allowed_categories=["recon", "scanning", "web", "credential_testing", "post_exploitation"]
    )
    assert len(matching_guides(scope, "all")) == len(PHASE_GUIDES)


def test_format_methodology_unknown_phase_message():
    scope = Scope(allowed_categories=["recon"])
    out = format_methodology(scope, "nonexistent")
    assert "No matching phase" in out


def test_format_methodology_renders_headings():
    scope = Scope(allowed_categories=["recon"], authorized_targets=["10.0.0.5"])
    out = format_methodology(scope, "recon")
    assert out.startswith("# Assessment Plan")
    assert "## Recon" in out
    assert "10.0.0.5" in out


def test_tool_inventory_covers_all_catalog_categories():
    statuses = tool_inventory()
    assert statuses
    assert all(isinstance(s.installed, bool) for s in statuses)
    assert {"recon", "scanning", "web"}.issubset({s.category for s in statuses})
