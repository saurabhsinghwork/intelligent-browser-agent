"""Normalize browser tab/window metadata and choose the active context without owning agent decisions."""
# Normalize raw tab list to guarantee tab index, title, url, and active fields.
def normalize_tabs(tabs: list[dict]) -> list[dict]:
    """Ensure tab dictionaries contain uniform index, url, title, and active fields.

    Args: tabs: List of raw tab dictionaries.
    Returns: Cleaned list of tab dictionaries.
    Side effects: None.
    Failure cases: None.
    """
    # Create empty list for normalized tabs.
    normalized = []
    # Process each tab mapping.
    for i, tab in enumerate(tabs or []):
        # Skip malformed transport entries instead of fabricating active contexts.
        if isinstance(tab, dict):
            # Extract url with fallback.
            url = str(tab.get("url", ""))
            # Extract title with fallback.
            title = str(tab.get("title", ""))
            # Extract active boolean flag.
            active = bool(tab.get("active", False))
            # Format normalized tab record with index.
            normalized.append({"index": i, "id": str(tab.get("id", i)), "url": url, "title": title, "active": active})
    # Return normalized tabs list.
    return normalized
# Select a sensible active tab from adapter-provided tab records.
def choose_active_tab(tabs: list[dict], current_url: str = "") -> dict | None:
    """Prefer the tab matching the current URL, then the adapter-marked active tab, otherwise the first tab.

    Args:
        tabs: List of tab dictionaries.
        current_url: Optional URL of currently observed page.

    Returns:
        Selected active tab dictionary, or None if tabs list is empty.

    Side effects:
        None.

    Failure cases:
        None; returns None when no tabs are open.
    """
    # Return no tab when the browser has no open pages.
    if not tabs:
        # A missing page is an explicit absent context, never implicit tab zero.
        return None
    # Prefer a tab whose URL matches the current observed page.
    for tab in tabs:
        # Match the actual observed URL before considering fallback metadata.
        if current_url and tab.get("url") == current_url:
            # Preserve this concrete adapter-supplied context.
            return tab
    # Use an explicitly active tab if the adapter supplies that signal.
    for tab in tabs:
        # Honor the runtime's actual active flag when no URL matches.
        if tab.get("active"):
            # Return the observed active context rather than inventing another page.
            return tab
    # Fall back deterministically to the first available tab.
    return tabs[0]
