"""Unit tests for website candidate validation and normalization."""
# Import candidate normalization functions.
from services.website_discovery import normalize_candidate, normalize_candidates
# Encode a controlled Bing-style destination wrapper.
import base64
# Ensure a bare domain is normalized to HTTPS.
def test_normalize_bare_domain():
    # Arrange a search result with a bare domain.
    result = normalize_candidate("Example", "example.com")
    # Assert a safe normalized candidate is returned.
    assert result is not None and result.url == "https://example.com"
# Reject non-web schemes.
def test_reject_unsafe_scheme():
    # Attempt to normalize a script URL as a website candidate.
    assert normalize_candidate("Bad", "javascript:alert(1)") is None
# Deduplicate candidates by domain and cap at five.
def test_deduplicates_candidates():
    # Arrange duplicate domains and one different domain.
    raw = [{"name":"A","url":"https://a.example"},{"name":"A duplicate","url":"https://a.example/path"},{"name":"B","url":"https://b.example"}]
    # Normalize the result list.
    result = normalize_candidates(raw)
    # Assert duplicate hostnames are collapsed.
    assert [item.domain for item in result] == ["a.example", "b.example"]
# Empty query must be rejected before calling any search provider.
def test_search_empty_query_raises():
    import pytest
    from services.website_discovery import search_websites
    # Assert whitespace or empty string raises ValueError.
    with pytest.raises(ValueError, match="Enter a website name"):
        search_websites("   ")
# Dynamic search uses injected function and normalizes candidates.
def test_search_with_injected_provider():
    from services.website_discovery import search_websites
    # Arrange injected provider returning two sites.
    fake_search = lambda q: [{"name": "Site One", "url": "https://one.example"}, {"name": "Site Two", "url": "https://two.example"}]
    results = search_websites("example query", search_fn=fake_search)
    assert len(results) == 2
    assert results[0].domain == "one.example"


# Search tracking wrappers should not become the user's selected website boundary.
def test_normalize_unwraps_encoded_search_destination():
    """Return the actual site from a known URL-safe base64 search wrapper."""
    # Encode one harmless direct website destination.
    encoded = base64.urlsafe_b64encode(b"https://www.linkedin.com/").decode("ascii").rstrip("=")
    # Build the same wrapper field shape returned by common Bing result links.
    wrapped = "https://www.bing.com/ck/a?u=a1" + encoded + "&tracking=ignored"
    # Normalize through the production discovery boundary.
    result = normalize_candidate("LinkedIn", wrapped)
    # The selected URL and hostname must be the actual website, not the search tracker.
    assert result is not None and result.domain == "www.linkedin.com" and result.url == "https://www.linkedin.com/"
