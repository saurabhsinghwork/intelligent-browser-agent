"""Clean only explicitly named local-fixture processes left by failed diagnostics.

Run with one or more exact run-artifact UUIDs. Eligible profiles are derived only
from loopback fixture URLs in those runs' own events. No files or profiles are
deleted, and unrelated browser processes are never matched by executable name.
"""
# Read explicit diagnostic UUID arguments without executing their contents.
import sys
# Resolve managed artifacts and profile paths.
from pathlib import Path
# Decode only the selected runs' own event data.
import json
# Recognize loopback fixture URLs in safe status events.
import re
# Compare actual browser start times with the diagnostic's timestamp.
from datetime import datetime
# Inspect and stop only proved local diagnostic process identities.
import psutil
# Resolve imports for this explicit maintenance entry point.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Reuse the application's checked exact-host/method profile convention.
from browser.session_manager import session_path
# Restrict candidate profile methods to the approved executors.
from config.constants import BROWSER_METHODS

# Keep eligible profile boundaries associated with their diagnostic start time.
profiles = {}
# Require concrete artifact identifiers rather than scanning or killing all browsers.
for identifier in sys.argv[1:]:
    # Refuse path traversal or arbitrary filesystem targets.
    if not re.fullmatch(r"[0-9a-f]{32}", identifier):
        # Stop before process operations on malformed input.
        raise ValueError("Expected an exact run-artifact UUID")
    # Read only the explicitly named diagnostic's own status events.
    path = Path(__file__).resolve().parents[1] / "data" / "run_artifacts" / identifier / "events.jsonl"
    # Preserve eligible test evidence while finding its own private fixture origin.
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    # The diagnostic must have recorded actual initialization before browser startup.
    started = datetime.fromisoformat(events[0]["timestamp"]).timestamp() - 1
    # Inspect only source status messages, without reading browser profiles or cookies.
    for event in events:
        # Only local synthetic fixtures qualify for this diagnostic cleanup utility.
        for url in re.findall(r"http://127\.0\.0\.1:\d+/[a-z_]+\.html", event.get("message", "")):
            # Each actual method owns a separate managed profile.
            for method in BROWSER_METHODS:
                # Retain only a computed path under the application's validated session root.
                profiles[str(session_path(url, method)).lower().replace("\\", "/")] = started
# Retain concrete process handles so PID reuse cannot expand cleanup authority.
owned = {}
# Inspect process metadata without displaying unrelated command lines.
for process in psutil.process_iter(["pid", "cmdline", "create_time"]):
    # Processes may exit while a failed diagnostic is being cleaned.
    try:
        # Require both exact diagnostic profile and compatible process creation time.
        if any(process.info["create_time"] >= started and any(profile in argument.lower().replace("\\", "/") for argument in process.info["cmdline"] or []) for profile, started in profiles.items()):
            # Retain only the proved diagnostic process and its own helper descendants.
            for child in [process, *process.children(recursive=True)]:
                # Preserve actual process identity, never a global executable-name pattern.
                owned[child.pid] = child
    # An unrelated inaccessible or already closed process is not a cleanup target.
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Continue checking only the explicitly selected diagnostic profiles.
        continue
# Terminate only those concrete proved diagnostic processes.
for process in reversed(list(owned.values())):
    # Browser helpers may have already exited with their parent.
    try:
        # No profile data or source artifacts are deleted.
        process.terminate()
    # Exit races never authorize another process operation.
    except psutil.Error:
        # Continue cleaning the remaining proved inventory.
        pass
# Report only the count of this utility's owned diagnostic targets.
print({"diagnostic_processes_terminated": len(owned)})
