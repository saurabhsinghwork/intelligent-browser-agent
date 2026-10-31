"""Protect the failures observed during the requirements audit.

These tests use no credentials or external websites. They distinguish source fidelity,
honest completion, model action parsing, and navigation authorization so a successful
mock transport cannot hide an incorrect application outcome.
"""
# Build lightweight SDK-shaped responses without making network requests.
from types import SimpleNamespace
# Parametrize the same model behavior across the two existing provider adapters.
import pytest
# Exercise the actual shared graph nodes rather than a duplicate implementation.
from agent.nodes import act_node, verify_node
# Inspect declared state channels that LangGraph persists between node calls.
from agent.state import AgentState
# Exercise actual navigation-boundary and observation behavior.
from browser.base import BaseBrowserAdapter
from browser.observation_builder import build_observation
# Construct normalized browser observations and agent decisions.
from domain.models import AgentDecision, BrowserObservation
# Keep the historical provider import until its compatibility alias is introduced.
from models.gemini_provider import GeminiProvider
from models.grok_provider import GrokProvider


# Both providers must preserve a navigation action even on text-heavy pages.
@pytest.mark.parametrize("provider_kind", ["gemini", "groq"])
def test_long_page_does_not_turn_click_into_finish(provider_kind):
    """A click without final output remains a click; ordinary actions need no answer."""
    # Return an ordinary next action using the SDK response's expected shape.
    raw = '{"kind":"click","target":"e1","output":""}'
    # Supply Gemini's models resource with a deterministic response method.
    gemini = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text=raw)))
    # Supply Groq's chat completion resource with its matching response shape.
    groq = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=raw))]))))
    # Select one provider instance with injected transport and a non-secret dummy key.
    provider = GeminiProvider("test", client=gemini) if provider_kind == "gemini" else GrokProvider("test", client=groq)
    # Reproduce the previous fallback threshold with realistic landing-page content.
    observation = BrowserObservation(url="https://example.com", text="Landing page. " * 20)
    # Ask the actual adapter to parse its supplied next action.
    decision = provider.decide("Click the requested product", observation, [])
    # Reject any substitution of current page text for the intended action.
    assert decision.kind == "click"


# Source formatting must remain intact before any presentation is chosen.
def test_observation_preserves_indentation_and_blank_lines():
    """Rendered code and meaningful line breaks survive observation normalization."""
    # Include indentation and blank lines that the previous compacting code removed.
    source = "Example\n\n    if ready:\n        print('yes')\n"
    # Build an observation through the public shared normalization function.
    observation = build_observation("https://example.com", "Demo", source, [], None)
    # Compare complete source strings instead of checking a convenient substring.
    assert observation.text == source


# A populated webpage is not proof that a claimed answer exists on that page.
def test_verification_rejects_invented_answer():
    """An invented price cannot be marked verified against unrelated page evidence."""
    # Return unrelated visible text from an otherwise functioning browser.
    adapter = SimpleNamespace(observe=lambda: BrowserObservation(url="https://example.com", text="No product price here."))
    # Ask the real verifier to assess an unsupported candidate result.
    result = verify_node({"adapter": adapter, "candidate_finish": True, "output": "Invented price: $999"})
    # The result must remain unverified even though its output is nonempty.
    assert not result.get("verified", False)


# Genuine blockers must never be converted to task success by text length.
def test_blocked_decision_stays_blocked():
    """A denied page can contain abundant text without satisfying the user's task."""
    # Construct the same blocked decision that a provider may legitimately return.
    decision = AgentDecision(kind="blocked", rationale="Access is unavailable")
    # Execute only terminal-decision handling, without requiring a live browser.
    result = act_node({"decision": decision.__dict__, "observation": {"text": "Access denied. " * 20}})
    # An explicit blocker must survive instead of becoming candidate completion.
    assert result.get("blocker") == "Access is unavailable"


# One selected website family includes ordinary regional and service subdomains.
def test_subdomain_in_selected_site_family_is_autonomous():
    """Avoid repeated prompts when one website moves among its own sibling hosts."""
    # Create the common policy object without launching any browser process.
    adapter = BaseBrowserAdapter()
    # Select the base website before it redirects to an ordinary sibling host.
    adapter.set_site("https://example.com", False)
    # The current autonomous policy treats the sibling as the same website family.
    assert adapter.is_allowed_url("https://shop.example.com")
    # A visually similar unrelated domain must remain outside the family.
    assert not adapter.is_allowed_url("https://example.com.evil.test")


# Error/outcome values must survive actual LangGraph state merging.
def test_graph_declares_failure_and_outcome_channels():
    """Recovery receives specific failures and verification receives action outcomes."""
    # Check the contract that LangGraph uses to create persisted state channels.
    assert {"last_error", "last_outcome"}.issubset(AgentState.__annotations__)
