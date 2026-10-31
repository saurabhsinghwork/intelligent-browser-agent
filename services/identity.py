"""Canonical website, page, and entity identities shared across the agent.

Navigation still uses real HTTP(S) URLs. Canonical identities remove transport and
tracking noise only when comparing evidence, page visits, and task progress.
"""
# Decode percent-encoded search redirects without evaluating their contents.
import base64
# Match stable entity identifiers and tracking parameter families.
import re
# Parse and rebuild URLs using the standard library.
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse


# Public suffix patterns that need one additional hostname label for a site family.
_SECOND_LEVEL_SUFFIXES = {"co.uk", "com.au", "co.in", "co.jp", "com.br", "com.sg", "co.nz", "co.za"}
# Query fields that report attribution rather than selecting displayed content.
_TRACKING_FIELDS = {"refid", "trackingid", "original_referer", "lipi", "trk", "fclid", "gclid", "fbclid", "msclkid"}


# Return a conservative registrable-site family without a network suffix lookup.
def site_family(hostname):
    """Return the normalized site family used for safe sibling-subdomain navigation."""
    # Normalize an absent or mixed-case host before comparison.
    host = str(hostname or "").strip(".").lower()
    # Preserve empty hosts for the caller's ordinary URL validation.
    if not host:
        # An empty host cannot authorize any destination.
        return ""
    # IP addresses and localhost-like names must remain exact boundaries.
    if host == "localhost" or re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        # Do not reinterpret an address as a public domain family.
        return host
    # Split only real DNS labels.
    labels = host.split(".")
    # One-label development hosts remain unchanged.
    if len(labels) < 2:
        # Preserve the exact local hostname.
        return host
    # Inspect the last two labels for common country-code second-level suffixes.
    suffix = ".".join(labels[-2:])
    # A known compound suffix requires one additional registrable label.
    if suffix in _SECOND_LEVEL_SUFFIXES and len(labels) >= 3:
        # Return the registrable label plus its compound public suffix.
        return ".".join(labels[-3:])
    # Ordinary domains use the final two labels as their site family.
    return ".".join(labels[-2:])


# Decode common search-result wrappers before they become selected destinations.
def unwrap_search_redirect(url):
    """Return an embedded HTTP(S) destination when a known search wrapper exposes one."""
    # Preserve surrounding URL text only after normalizing whitespace.
    clean = str(url or "").strip()
    # Parse the supplied result without following a network redirect.
    parsed = urlparse(clean)
    # Read query fields in their original order.
    fields = dict(parse_qsl(parsed.query, keep_blank_values=True))
    # Search engines commonly expose a direct destination in one of these fields.
    for name in ("uddg", "url", "target", "dest", "destination"):
        # Decode the candidate only when it exists.
        candidate = unquote(fields.get(name, ""))
        # Accept only an explicit web destination.
        if candidate.lower().startswith(("http://", "https://")):
            # Return the actual destination rather than the search tracking host.
            return candidate
    # Bing frequently stores a URL-safe base64 destination in its `u` field.
    encoded = fields.get("u", "")
    # The documented wrapper prefix distinguishes encoded URLs from ordinary query values.
    if encoded.startswith("a1"):
        # Remove the wrapper marker before URL-safe decoding.
        payload = encoded[2:]
        # Add only the padding needed by the base64 decoder.
        payload += "=" * (-len(payload) % 4)
        # Invalid search metadata must leave the original real result untouched.
        try:
            # Decode without interpreting the resulting text as code.
            candidate = base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8")
        # Malformed or non-UTF8 values are ordinary non-unwrapped results.
        except (ValueError, UnicodeError):
            # Preserve the original URL below.
            candidate = ""
        # Accept only a decoded HTTP(S) destination.
        if candidate.lower().startswith(("http://", "https://")):
            # Return the user-relevant endpoint.
            return candidate
    # No supported wrapper exposed a trustworthy direct destination.
    return clean


# Produce one stable comparison key while retaining content-changing query fields.
def canonical_url(url):
    """Remove fragments and tracking noise, normalize the site family, and preserve content state."""
    # Parse the real URL supplied by an observation or link.
    parsed = urlparse(str(url or ""))
    # Non-web and relative values cannot form a cross-page identity here.
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        # Preserve the original value for explicit validation elsewhere.
        return str(url or "")
    # Keep meaningful query fields in their original order.
    retained = []
    # A stable path entity ID makes list-position attribution non-content-bearing.
    stable_path_entity = bool(re.search(r"(?:^|[-/])(?:[0-9]{6,}|[0-9a-f]{8}-[0-9a-f-]{20,})(?:/|$)", parsed.path, re.I))
    # Inspect each field independently so one tracker cannot remove real filters.
    for name, value in parse_qsl(parsed.query, keep_blank_values=True):
        # Compare names case-insensitively.
        lowered = name.lower()
        # Attribution fields and UTM families do not change requested page content.
        if lowered in _TRACKING_FIELDS or lowered.startswith("utm_") or stable_path_entity and lowered in {"position", "pagenum"}:
            # Omit only the known tracking field.
            continue
        # Preserve search terms, locations, pagination, filters, and unknown fields.
        retained.append((name, value))
    # Collapse sibling website hosts into one task-site family for comparison.
    host = site_family(parsed.hostname)
    # Preserve a nondefault port when one is present.
    netloc = host + ((":" + str(parsed.port)) if parsed.port else "")
    # Normalize an empty web path to the root page.
    path = parsed.path or "/"
    # Rebuild without credentials or fragments.
    return urlunparse((parsed.scheme.lower(), netloc, path, "", urlencode(retained, doseq=True), ""))


# Identify a logical record independently from its current tracking URL.
def entity_identity(url, fallback=""):
    """Return a stable entity URL/key or a caller-provided structural fallback."""
    # Canonicalize before extracting a stable trailing identifier.
    normalized = canonical_url(url)
    # Read the path without depending on one named website.
    parsed = urlparse(normalized)
    # Numeric and UUID-like path identifiers commonly define products, jobs, and records.
    match = re.search(r"(?:^|[-/])([0-9]{6,}|[0-9a-f]{8}-[0-9a-f-]{20,})(?:/|$)", parsed.path, re.I)
    # Prefer the site family plus concrete stable identifier when available.
    if match:
        # Keep identities compact while separating unrelated sites.
        return site_family(parsed.hostname) + ":" + match.group(1).lower()
    # Check query parameters for explicit entity identifiers (e.g. currentJobId, jobId, productId, id).
    for q_name, q_val in parse_qsl(parsed.query, keep_blank_values=True):
        # Match parameter names indicating unique item or record identifiers.
        if re.search(r"\b(jobid|currentjobid|productid|itemid|articleid|id|sku)\b", q_name, re.I):
            # Validate that query value is a numeric ID or standard UUID.
            if re.match(r"^[0-9]{5,}$|^[0-9a-f]{8}-[0-9a-f-]{20,}$", q_val, re.I):
                # Return qualified site family and entity identifier.
                return site_family(parsed.hostname) + ":" + q_val.lower()
    # Search or listing pages do not define a single entity; prefer caller-provided structural fallback.
    is_listing_page = bool(re.search(r"(?:^|/)(?:search|jobs/search|find|browse|catalog|results|category)(?:/|$|\?)", parsed.path, re.I))
    # Listing page URLs without specific query IDs should use caller structural fallback.
    if fallback and is_listing_page:
        # Return caller-provided fallback for listing containers.
        return str(fallback)
    # When no entity identifier is in the URL, a non-empty fallback retains the caller's specific key.
    if fallback and not normalized:
        # Return caller-provided fallback for empty URLs.
        return str(fallback)
    # An explicit item-level canonical href remains stronger than a transient DOM identifier.
    if normalized and not is_listing_page:
        # Preserve the complete content-selecting canonical URL.
        return normalized
    # Structural callers retain their best deterministic fallback.
    return str(fallback or normalized or "")
