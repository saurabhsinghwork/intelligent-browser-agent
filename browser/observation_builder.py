"""Normalize complete source observations without changing their wording or whitespace."""
# Import the observation contract.
from domain.models import BrowserObservation
# Convert supplied browser data into the shared source-preserving observation contract.
def build_observation(url: str, title: str, text: str, elements: list[dict], screenshot_path: str | None, tabs: list[dict] | None = None, max_chars: int = 24000, all_screenshots: list[str] | None = None) -> BrowserObservation:
    """Preserve complete page text and supplied targets while supporting older test controllers.

    Args:
        url: Current browser page URL.
        title: Current page title.
        text: Raw page innerText.
        elements: List of element dictionaries.
        screenshot_path: Local path to saved screenshot or None.
        tabs: List of open tab dictionaries or None.
        max_chars: Legacy compatibility argument; deliberately ignored to prevent source truncation.
        all_screenshots: Optional list of all captured screenshots during progressive scrolls.

    Returns:
        A normalized BrowserObservation instance.

    Side effects:
        None.

    Failure cases:
        None; handles empty or malformed element inputs gracefully.
    """
    # Preserve raw UI text; navigation prompts apply their own separate context limits.
    compact_text = text or ""
    # Normalize elements to guarantee an index label (e.g. e0, e1) for model targeting.
    normalized_elements = []
    # Preserve all supplied elements; only the separate navigation prompt has a context budget.
    for i, elem in enumerate(elements or []):
        # Ignore malformed entries rather than inventing actionable browser targets.
        if isinstance(elem, dict):
            # Create a shallow copy to prevent mutating adapter data.
            item = dict(elem)
            # Ensure id label exists for model reference.
            if "id_label" not in item:
                # Legacy labels remain metadata; live adapters use real stable DOM references.
                item["id_label"] = f"e{i}"
            # Keep caller-owned element dictionaries unchanged.
            normalized_elements.append(item)
    # Assemble all screenshots list including primary screenshot.
    all_shots = list(all_screenshots or [])
    # Retain a current image that was not already present in capture history.
    if screenshot_path and screenshot_path not in all_shots:
        # Preserve actual image order instead of overwriting an earlier reference.
        all_shots.append(screenshot_path)
    # Return a common record usable by either model provider.
    return BrowserObservation(url=url or "", title=title or "", text=compact_text, elements=normalized_elements, screenshot_path=screenshot_path, tabs=tabs or [], all_screenshots=all_shots)
