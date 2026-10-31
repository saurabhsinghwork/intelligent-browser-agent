"""Verify exact source retention, logical-record deduplication, and complete exports.

These tests compare captured source directly. They do not mirror model-generated
answers or treat a plausible output length as evidence of correctness.
"""
# Decode the independently inspectable provenance manifest.
import json
# Exercise the actual durable collector output rather than a mock formatter.
from services.evidence import EvidenceStore
# Verify model context limits cannot change preserved raw observations.
from models.base import decision_prompt
# Supply complete source text to the actual navigation prompt builder.
from domain.models import BrowserObservation


# Preserve code, repeated values, Unicode, and all source text beyond prompt limits.
def test_exact_source_and_large_exports(tmp_path):
    """Keep full text and relationships while navigation context stays bounded."""
    # Allocate only this test's evidence database.
    store = EvidenceStore(tmp_path)
    # Include content longer than the navigation excerpt limit.
    code = "if ready:\n    print('₹1,299.00')\n\n" + ("    # original source\n" * 2000)
    # Two equal-valued UI records are separate legitimate source entries.
    blocks = [{"key": "code", "kind": "code", "text": code, "y": 0, "x": 0}, {"key": "row-1", "kind": "p", "text": "Same value", "y": 100, "x": 0}, {"key": "row-2", "kind": "p", "text": "Same value", "y": 200, "x": 0}]
    # Capture actual source relationships and URL.
    capture = {"url": "https://example.com/article", "blocks": blocks}
    # Store source once and then reproduce an overlapping viewport capture.
    store.add(capture, "main", 0, 0)
    # Idempotence removes only the repeated capture, not equal values with distinct keys.
    store.add(capture, "main", 0, 0)
    # Exact source must remain byte-for-byte intact within each block.
    assert store.blocks()[0]["text"] == code
    # Legitimate repeated UI values must not be collapsed.
    assert len(store.blocks()) == 3
    # Model navigation context can be bounded without altering raw source.
    prompt = decision_prompt("Read this page", BrowserObservation("https://example.com", text=code), [])
    # The actual observation is larger than its model excerpt.
    assert len(prompt) < len(code)
    # Export complete source artifacts independently from the prompt.
    artifacts = store.export()
    # Preserve source code at its complete original length.
    assert open(artifacts["text"], encoding="utf-8").read().startswith(code)
    # Keep complete raw relationships in an independent manifest.
    assert json.load(open(artifacts["manifest"], encoding="utf-8"))["blocks"][0]["text"] == code
    # Release only the test-owned SQLite connection.
    store.close()


# Table semantics must survive without interpreting tabs or spaces as inferred columns.
def test_table_relationships_and_markdown_are_explicit(tmp_path):
    """Preserve exact cells and produce a valid contiguous Markdown table."""
    # Keep artifacts isolated in inherited-permission test storage.
    store = EvidenceStore(tmp_path)
    # Define actual source header and data relationships.
    rows = [{"key": "header", "kind": "table_row", "text": "Item\tPrice", "table": "table", "cells": [{"text": "Item", "header": True}, {"text": "Price", "header": True}], "y": 0}, {"key": "value", "kind": "table_row", "text": "Laptop\t₹1,299.00", "table": "table", "cells": [{"text": "Laptop"}, {"text": "₹1,299.00"}], "y": 30}]
    # Store the actual structured source.
    store.add({"url": "https://example.com", "blocks": rows}, "main", 0, 0)
    # Table header/separator/data must be contiguous rather than separate prose blocks.
    assert "| Item | Price |\n| --- | --- |\n| Laptop | ₹1,299.00 |" in store.markdown()
    # Raw exact text retains the original row values and cell delimiters.
    assert store.blocks()[1]["text"] == "Laptop\t₹1,299.00"
    # Release only this test's resources.
    store.close()


# Sticky chrome must not repeat when its measured scroll position changes.
def test_sticky_block_deduplicates_by_structure_not_scroll_position(tmp_path):
    """Store one fixed header across overlapping viewport captures."""
    # Allocate an isolated durable evidence store.
    store = EvidenceStore(tmp_path / "sticky")
    # Capture the same top-level header at two different measured coordinates.
    first = {"url": "https://www.example.com/results", "blocks": [{"key": "doc-a:12", "stable_path": "body>header>button:nth-of-type(1)", "persistent": True, "kind": "text", "text": "Join now", "y": 12, "x": 0}]}
    # A later viewport changes transient DOM identity and absolute y position.
    second = {"url": "https://example.com/results?utm_source=test", "blocks": [{"key": "doc-b:1612", "stable_path": "body>header>button:nth-of-type(1)", "persistent": True, "kind": "text", "text": "Join now", "y": 1612, "x": 0}]}
    # Persist both real captures.
    store.add(first, "body", 0, 0)
    # Canonical page and structural identity should make this insertion idempotent.
    store.add(second, "body", 0, 0)
    # Only one source block remains despite two screenshots/positions.
    assert [block["text"] for block in store.blocks()] == ["Join now"]
    # Release the test-owned database.
    store.close()
