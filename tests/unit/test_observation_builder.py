"""Verify complete source and target retention before separately bounded navigation prompts."""
# Import pytest.
import pytest
# Import observation builder.
from browser.observation_builder import build_observation

# Observation building preserves complete source while provider prompts bound navigation context.
def test_observation_builder_preserves_complete_text():
    """Retain whitespace and content beyond the former navigation-context cutoff."""
    # Arrange multi-line text with empty spaces and large payload.
    raw_text = "\n\n  Welcome to Demo  \n\n\n   Paragraph one   \n\n" + ("Long text " * 3000)
    obs = build_observation(url="https://example.com", title="Demo", text=raw_text, elements=[], screenshot_path="test.png")
    # Compare the complete source, including whitespace beyond the old context limit.
    assert obs.text == raw_text
    # Large source evidence must not silently disappear at the old prompt boundary.
    assert len(obs.text) > 24000

# Observation builder preserves all supplied targets without a hidden element cutoff.
def test_observation_builder_preserves_all_element_labels():
    """Keep late-page targets available instead of silently deleting controls after position 250."""
    # Arrange 300 raw element dicts.
    raw_elements = [{"tag": "button", "text": f"Button {i}"} for i in range(300)]
    obs = build_observation(url="https://example.com", title="Demo", text="Test", elements=raw_elements, screenshot_path=None)
    # Every supplied target remains in the full observation.
    assert len(obs.elements) == 300
    # Assert id_label assigned predictably.
    assert obs.elements[0]["id_label"] == "e0"
    assert obs.elements[10]["id_label"] == "e10"
