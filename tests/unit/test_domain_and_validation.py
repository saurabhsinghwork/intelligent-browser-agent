"""Unit tests for normalized decisions and website boundary enforcement."""
# Import pytest and domain/validation components.
import pytest
from domain.models import AgentDecision
from agent.validation import validate_decision
from browser.base import BaseBrowserAdapter
# Reject a navigation decision without a destination.
def test_navigation_requires_target():
    # Build a malformed navigation decision.
    decision = AgentDecision(kind="navigate")
    # Assert the validator rejects it before browser execution.
    with pytest.raises(ValueError, match="destination"):
        validate_decision(decision)
# Reject unauthorized navigation outside the selected website.
def test_domain_boundary_blocks_external_site():
    # Arrange an adapter locked to the selected site.
    adapter = BaseBrowserAdapter()
    adapter.set_site("https://example.com", False)
    # Assert an unrelated host is rejected.
    with pytest.raises(PermissionError, match="explicit authorization"):
        adapter.ensure_allowed_url("https://another.com")
# Allow an explicitly authorized external site.
def test_domain_boundary_allows_explicit_authorization():
    # Arrange the selected domain.
    adapter = BaseBrowserAdapter()
    adapter.set_site("https://example.com", False)
    # Assert explicit authorization allows the destination.
    adapter.ensure_allowed_url("https://another.com", external_authorized=True)
# Allow navigation when external domain is in configured authorized domains.
def test_domain_boundary_allows_configured_authorized_domains():
    # Arrange adapter with configured authorized domain list.
    adapter = BaseBrowserAdapter()
    adapter.set_site("https://example.com", False, authorized_domains=["oauth.provider.com"])
    # Assert destination host matching authorized domain succeeds without error.
    assert adapter.is_allowed_url("https://oauth.provider.com/login") is True
    assert adapter.is_allowed_url("https://forbidden.com") is False
# Require target for tab switching action.
def test_tab_action_requires_target():
    # Arrange a malformed switch_tab decision without target.
    decision = AgentDecision(kind="switch_tab", target=" ")
    # Assert validator rejects it.
    with pytest.raises(ValueError, match="target tab"):
        validate_decision(decision)
