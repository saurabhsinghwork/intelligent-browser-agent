"""Actual keyless website discovery with safe URL normalization.

Discovery queries a real search service. It never manufactures domain variations
to fill an arbitrary candidate count and does not require a reasoning-model key.
"""
# Normalize exact hostnames and reject unsafe schemes.
from urllib.parse import urlparse
# Keep the established candidate record shared with the UI.
from domain.models import WebsiteCandidate
# Bound the number of real choices offered to the user.
from config.constants import MAX_WEBSITE_CANDIDATES
# Prefer direct search destinations over tracking-wrapper hostnames.
from services.identity import unwrap_search_redirect


# Validate one real result without silently changing its intended host.
def normalize_candidate(name, url):
    """Return a safe HTTP(S) candidate or None for malformed/credential-bearing URLs."""
    # Normalize surrounding transport whitespace only.
    clean = unwrap_search_redirect(str(url).strip())
    # Reject arbitrary schemes rather than treating them as bare hostnames.
    if ":" in clean and not clean.lower().startswith(("http://", "https://")):
        # JavaScript, data, and file destinations are never discovery suggestions.
        return None
    # Accept a user-supplied bare domain as an explicit direct candidate.
    normalized = clean if clean.lower().startswith(("http://", "https://")) else "https://" + clean
    # Parse the actual hostname rather than testing substrings.
    parsed = urlparse(normalized)
    # Require a usable host and prohibit embedded credentials.
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or "." not in parsed.hostname or " " in parsed.hostname or parsed.username or parsed.password:
        # Do not offer malformed or secret-bearing destinations.
        return None
    # Remove fragments while preserving meaningful paths and query parameters.
    return WebsiteCandidate(name=str(name).strip() or parsed.hostname, domain=parsed.hostname.lower(), url=parsed._replace(fragment="").geturl())


# Normalize real provider results and deduplicate their exact hostnames.
def normalize_candidates(results):
    """Preserve source ranking, reject malformed entries, and return at most five sites."""
    # Keep original ranking and a concrete seen-host set.
    candidates, seen = [], set()
    # Process only actual supplied results.
    for item in results:
        # Support both current DDGS and injected search-provider field names.
        candidate = normalize_candidate(item.get("name", item.get("title", "")), item.get("url", item.get("href", "")))
        # Skip malformed or repeated hostnames without inventing replacement domains.
        if candidate is None or candidate.domain in seen:
            # Other real results may still provide enough relevant choices.
            continue
        # Preserve this actual safe candidate.
        candidates.append(candidate)
        # Record the exact host after normalization.
        seen.add(candidate.domain)
        # Bound user-facing choices as specified.
        if len(candidates) == MAX_WEBSITE_CANDIDATES:
            # Stop after five real distinct choices.
            break
    # Fewer than three results remain an honest search outcome.
    return candidates


# Search on explicit user action without requiring a model credential.
def search_websites(query, search_fn=None, api_key=None, provider="gemini"):
    """Query actual web search and return real candidates; raise actionable service errors.

    api_key/provider remain accepted for UI compatibility but are not needed. Search
    engines interpret ordinary misspellings; no model-generated URL is trusted.
    """
    # Reject empty queries before any network request.
    clean = query.strip()
    # A blank search cannot identify the user's intended website.
    if not clean:
        # Preserve the established validation contract.
        raise ValueError("Enter a website name or partial domain to search.")
    # Explicit domain input may appear before real search results.
    direct = normalize_candidate(clean, clean) if "." in clean else None
    # Tests or other actual search connectors may inject a provider.
    if search_fn is not None:
        # Preserve the caller's actual source data.
        raw = search_fn(clean)
    # Production always queries a real search service.
    else:
        # Load the keyless search dependency only when Search is clicked.
        from ddgs import DDGS
        # Keep individual discovery requests bounded.
        try:
            # Request real ranked results, allowing the engine to correct misspellings.
            raw = list(DDGS(timeout=12).text(clean + " official website", max_results=15))
        # A failed search must never be replaced with guessed domains.
        except Exception as exc:
            # An explicitly entered valid URL remains usable when search is unavailable.
            if direct is not None:
                # This is user-supplied input, not an invented fallback suggestion.
                return [direct]
            # Keep the exception type without raw network/authentication payloads.
            raise RuntimeError("Website search is unavailable; retry the search or enter a full website URL. " + type(exc).__name__) from exc
    # Preserve direct explicit input without requiring a successful search response.
    ordered = ([{"name": direct.name, "url": direct.url}] if direct else []) + list(raw)
    # Return only validated real results, up to the requested maximum.
    return normalize_candidates(ordered)
