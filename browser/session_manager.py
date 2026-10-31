"""Safe reusable session paths isolated by exact host and browser method.

All recursive clearing resolves and verifies concrete targets inside the configured
session root before deletion. Source URLs, credentials, and cookies are not logged.
"""
# Build explicit local paths and stable nonsecret directory identities.
from pathlib import Path
# Hash exact host/origin identities without disclosing paths or query secrets.
import hashlib
# Normalize exact hostnames instead of hashing every unrelated path/query separately.
from urllib.parse import urlparse
# Remove only verified application-owned profile directories.
import shutil
# Restrict method names so callers cannot escape the session root.
from config.constants import BROWSER_METHODS

# Keep profiles local to the project, independent of the launching working directory.
SESSION_ROOT = Path(__file__).resolve().parents[1] / "data" / "sessions"


# Resolve one concrete isolated profile directory.
def session_path(site, method, root=SESSION_ROOT):
    """Return a stable exact-host/method path; reject unsafe method identifiers."""
    # Method names are directory components, so validate them before joining paths.
    if method not in BROWSER_METHODS:
        # Prevent traversal such as ../ from ever reaching filesystem operations.
        raise ValueError("Unsupported browser session method")
    # Accept explicit URLs or a bare host at this configuration boundary.
    parsed = urlparse(site if "://" in site else "https://" + site)
    # Isolate by exact host while preserving a distinct port for local/test origins.
    identity = (parsed.hostname or "").lower() + (":" + str(parsed.port) if parsed.port else "")
    # Reject a missing host instead of mixing malformed sessions.
    if not parsed.hostname:
        # Keep invalid configuration actionable.
        raise ValueError("Session site needs a hostname")
    # Do not embed potentially secret paths or queries in profile names.
    key = hashlib.sha256(identity.encode()).hexdigest()[:16]
    # Use Browser Use's documented managed-profile naming convention to prevent temporary profile copies.
    # Resolve absolute paths before any later deletion safety check.
    return Path(root).resolve() / method / (("browser-use-user-data-dir-" + key) if method == "browser_use" else key)


# Create only a validated session directory.
def ensure_session_dir(site, method, root=SESSION_ROOT):
    """Create the isolated profile directory and return its absolute path."""
    # Validate all path components before filesystem writes.
    target = session_path(site, method, root)
    # Inherit normal workspace permissions instead of restrictive test-only ACLs.
    target.mkdir(parents=True, exist_ok=True)
    # Return the actual profile path used by the selected browser.
    return target


# Report profile data presence without claiming authentication is still valid.
def has_session(site, method, root=SESSION_ROOT):
    """Return whether the compatible profile contains data; browser tests verify actual reuse."""
    # Use exactly the same isolation rule as creation and cleanup.
    target = session_path(site, method, root)
    # An existing empty directory is not saved browser state.
    return target.is_dir() and any(target.iterdir())


# Remove one profile only after resolving its workspace boundary.
def clear_session(site, method, root=SESSION_ROOT):
    """Delete a verified isolated profile; return False when none exists."""
    # Resolve the intended permitted root independently from a computed target.
    boundary = Path(root).resolve()
    # Compute and resolve the exact final deletion target.
    target = session_path(site, method, boundary).resolve()
    # Symlinks or malformed components must never redirect deletion outside the root.
    if not target.is_relative_to(boundary) or target == boundary:
        # Refuse destructive operations when their boundary cannot be established.
        raise ValueError("Session deletion escaped its configured root")
    # Remove only an actual isolated directory.
    if target.is_dir():
        # The absolute final target has been verified above.
        shutil.rmtree(target)
        # Report a real removal.
        return True
    # Absence is not an exceptional cleanup failure.
    return False


# Clear compatible saved profiles without deleting unknown directories.
def clear_all_sessions(root=SESSION_ROOT):
    """Remove verified profiles under approved methods; retain unrelated root contents."""
    # Resolve the explicit intended cleanup boundary first.
    boundary = Path(root).resolve()
    # A nonexistent session root contains no profiles.
    if not boundary.is_dir():
        # Avoid creating a root merely to clear nothing.
        return 0
    # Count only directories actually removed.
    count = 0
    # Restrict clearing to documented browser methods.
    for method in BROWSER_METHODS:
        # Resolve method directories before enumerating their profile children.
        method_dir = (boundary / method).resolve()
        # Reject linked method roots outside the intended session storage.
        if not method_dir.is_relative_to(boundary) or not method_dir.is_dir():
            # Unknown/missing storage is not silently treated as an owned profile.
            continue
        # Snapshot children before removing individual profile directories.
        for child in list(method_dir.iterdir()):
            # Resolve the concrete final deletion target.
            target = child.resolve()
            # Browser Use recognizes this managed-profile prefix and otherwise silently copies Chrome profiles.
            identity = child.name.removeprefix("browser-use-user-data-dir-") if method == "browser_use" else child.name
            # Profiles remain stable hexadecimal identities, never arbitrary directories.
            if target.is_dir() and target.is_relative_to(method_dir) and len(identity) == 16 and all(character in "0123456789abcdef" for character in identity):
                # The final absolute target has been checked against the intended boundary.
                shutil.rmtree(target)
                # Report only real scoped removals.
                count += 1
    # Keep the configured root and other application artifacts.
    return count
