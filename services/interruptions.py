"""Recognize and dismiss nonessential rendered overlays without site-specific selectors.

The classifier relies on visible control semantics and overlay structure. It never
targets a website name, CSS class from one site, or a coordinate guessed from an image.
"""
# Match semantic control labels and interruption purposes conservatively.
import re
# Dispatch the same provider-neutral click used by every browser executor.
from domain.models import AgentDecision


# Mark application-owned optional-overlay clicks without changing the public action language.
DISMISS_ACTION_VALUE = "__iba_optional_overlay__"


# Labels that unambiguously decline or close an optional rendered interruption.
_DISMISS_LABEL = re.compile(r"^(?:close|dismiss)(?:\s+[\w'-]+){0,5}$|^(?:not now|no thanks|maybe later|skip|continue as guest|continue without signing in)$|^[×✕✖x]$", re.I)
# Common purposes of optional overlays, expressed independently from any website.
_INTERRUPTION_PURPOSE = re.compile(r"\b(?:sign\s*in|sign\s*up|log\s*in|login|join\s+now|create\s+(?:an?\s+)?account|register|continue\s+with\s+(?:google|microsoft|email)|subscribe|newsletter|open\s+(?:the\s+)?app|better\s+on\s+the\s+app|install\s+(?:the\s+)?app|get\s+(?:the\s+)?app|enable\s+notifications?|turn\s+on\s+notifications?|special\s+offer|promotion)\b", re.I)
# Explicit authentication instructions make a sign-in interface task-relevant.
_LOGIN_OBJECTIVE = re.compile(r"\b(?:sign|log)\s+(?:me\s+)?in(?:\s+to)?\b|\bauthenticate\b", re.I)


# Build the label actually exposed to a user or accessibility client.
def dismiss_label(element):
    """Return a normalized visible/accessibility label for one observed control."""
    # Prefer rendered text, then accessibility and title fallbacks used by icon buttons.
    for key in ("text", "aria_label", "title"):
        # Normalize only surrounding whitespace without rewriting the label.
        value = str(element.get(key, "")).strip()
        # Return the first user-facing label instead of duplicating equal text/ARIA values.
        if value:
            # Keep the actual observed wording for exact matching.
            return value
    # An unlabeled icon cannot be clicked automatically by this policy.
    return ""


# Select only a close control inside a recognized optional overlay.
def find_dismissible_interruption(elements, objective=""):
    """Return one grounded optional-overlay close control, or ``None`` when uncertain."""
    # Inspect controls in their observed DOM order for deterministic behavior.
    for element in elements or []:
        # Hidden, disabled, off-screen, or covered controls cannot receive reliable native input.
        if element.get("disabled") or element.get("in_view") is False or element.get("actionable") is False:
            # Continue without guessing a coordinate or hidden replacement.
            continue
        # A close-like word elsewhere on the page is not sufficient evidence of a popup.
        if not element.get("overlay"):
            # Preserve ordinary task controls and content disclosures.
            continue
        # Read the same visible/accessibility label used for native element resolution.
        label = dismiss_label(element)
        # Require a precise dismissal label rather than fuzzy similarity.
        if not _DISMISS_LABEL.fullmatch(label.strip()):
            # Avoid clicking arbitrary buttons within the overlay.
            continue
        # Classify the surrounding overlay by its rendered wording.
        context = str(element.get("overlay_context", ""))
        # Only known nonessential interruption purposes are automatically dismissed.
        if not _INTERRUPTION_PURPOSE.search(context):
            # Task dialogs such as filters remain under agent reasoning.
            continue
        # A requested authentication task must be handed to the user, not closed.
        if _LOGIN_OBJECTIVE.search(str(objective or "")) and re.search(r"\b(?:sign\s*in|log\s*in|login|authenticate)\b", context, re.I):
            # Preserve the required login UI for human assistance.
            continue
        # Return the exact current DOM identity used by all native click transports.
        return element
    # No adequately grounded optional interruption was observed.
    return None


# Dismiss one currently observed interruption through the normal guarded click path.
def dismiss_observed_interruption(adapter, observation, objective=""):
    """Dismiss one topmost optional overlay and return status plus the freshest observation."""
    # Support both shared observation records and capture-style mappings.
    elements = observation.elements if hasattr(observation, "elements") else observation.get("elements", [])
    # Select only a semantically supported optional overlay control.
    target = find_dismissible_interruption(elements, objective)
    # Leave the page unchanged when classification is uncertain.
    if target is None:
        # Tell the caller that no fresh observation is required.
        return False, observation
    # Read the immutable observation identity required by guarded model-equivalent input.
    observation_id = observation.observation_id if hasattr(observation, "observation_id") else observation.get("observation_id", "")
    # Use the same accurate element-bound native click and visible cursor path as every action.
    try:
        # Mark this narrowly as a close action so transports avoid an unnecessary pre-click hover race.
        adapter.execute(AgentDecision(kind="click", target=target["id_label"], value=DISMISS_ACTION_VALUE, observation_id=observation_id, rationale="Dismiss nonessential overlay"))
    # Stop remains authoritative and must never be converted into best-effort popup handling.
    except InterruptedError:
        # Preserve prompt cancellation through the ordinary controller path.
        raise
    # A stacked or transitioning overlay may replace the topmost target between observation and input.
    except Exception:
        # Re-observe once to resolve the new actual top layer rather than retrying a covered identity.
        refreshed = adapter.observe()
        # Select a newly grounded close control from that real resulting interface.
        replacement = find_dismissible_interruption(refreshed.elements, objective)
        # If the old interruption disappeared during the failed click, normal work may continue.
        if replacement is None:
            # Treat disappearance as successful handling without inventing a click outcome.
            return True, refreshed
        # Bind the one bounded retry to the fresh immutable observation.
        try:
            # Dispatch one native retry against only the current topmost close control.
            adapter.execute(AgentDecision(kind="click", target=replacement["id_label"], value=DISMISS_ACTION_VALUE, observation_id=refreshed.observation_id, rationale="Dismiss replacement nonessential overlay"))
        # Stop remains authoritative during the retry as well.
        except InterruptedError:
            # Preserve cancellation rather than continuing page collection.
            raise
        # Optional interruption handling must never consume all task retries.
        except Exception:
            # Record one concise diagnostic while allowing unobstructed DOM extraction to proceed.
            if adapter.monitor is not None:
                # Keep the warning free of raw website markup or private content.
                adapter.monitor.log("WARNING", "Optional overlay could not be dismissed after one grounded retry; continuing without failing the task")
            # Return the fresh interface so later task actions do not use a stale observation ID.
            return False, refreshed
    # Observe the actual post-click interface for stacked-overlay handling and stale-ID safety.
    refreshed = adapter.observe()
    # Report successful native dismissal with its resulting browser state.
    return True, refreshed
