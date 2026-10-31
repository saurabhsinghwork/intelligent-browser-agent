"""Thread-safe current-run events and explicit human-assistance state.

The worker subclass forwards these events to the parent UI. Complete logs/artifacts
remain on disk; the UI can render a bounded recent window without losing evidence.
"""
# Keep local monitor access safe between UI polling and worker coordination.
from threading import Event, RLock
# Serialize event records without treating dataclasses as dictionaries.
from dataclasses import asdict
# Redact secrets at the actual event boundary.
from domain.events import make_event, redact_secrets


# Own monitoring data for precisely one run.
class RunMonitor:
    """Collect status, safe events, immutable images, assistance, and Stop signaling."""

    # Allocate fresh state rather than retaining a previous run's result.
    def __init__(self):
        """Initialize safe local state; browser/provider initialization happens elsewhere."""
        # Coordinate concurrent updates and UI snapshots.
        self._lock = RLock()
        # Expose the current concise activity.
        self.status = "Ready"
        # Keep chronological typed events for existing integrations.
        self.logs = []
        # Preserve immutable screenshot references.
        self.screenshots = []
        # Allow both graph and local traversal to observe Stop.
        self.stop_event = Event()
        # Reflect actual worker ownership.
        self.active = False
        # Retain terminal state independently from progress.
        self.result = None
        # Freeze automatic input for a concrete user decision.
        self.waiting = {}

    # Publish safe current activity immediately.
    def update_status(self, status):
        """Set a bounded one-line status and append a redacted event."""
        # Keep lifecycle changes and their diagnostic event consistent.
        with self._lock:
            # Redact before storing user-visible status.
            self.status = redact_secrets(status)[:240]
            # Preserve chronological typed diagnostics.
            self.logs.append(make_event("INFO", self.status))

    # Preserve actionable diagnostics without provider secrets.
    def log(self, level, message):
        """Append a timestamped redacted diagnostic."""
        # Keep concurrent event ordering stable.
        with self._lock:
            # The event constructor owns redaction.
            self.logs.append(make_event(level, str(message)[:1200]))

    # Publish immutable viewport evidence as it is captured.
    def add_screenshot(self, path):
        """Record a screenshot once without reading or modifying the image."""
        # Preserve a consistent artifact inventory during UI polling.
        with self._lock:
            # Repeated references are not additional browser observations.
            if path not in self.screenshots:
                # Keep source capture order.
                self.screenshots.append(path)

    # Expose concrete assistance independently of task completion.
    def request(self, request):
        """Store a serializable waiting prompt; automatic execution must pause."""
        # Keep the prompt consistent with its visible status.
        with self._lock:
            # Copy request data so callers cannot mutate UI state afterward.
            self.waiting = dict(request)
            # Preserve the reason while avoiding raw SDK details.
            self.status = "Waiting: " + request.get("kind", "assistance")

    # Direct synchronous runs cannot invent a human response.
    def await_response(self):
        """Return None when no UI command channel is attached; worker monitors override this."""
        # Do not automatically approve an external host or authentication gate.
        return None

    # Signal cancellation without claiming the worker already finished.
    def stop(self):
        """Request Stop; the owning supervisor performs actual bounded cleanup."""
        # Graph nodes and every local collection loop share this signal.
        self.stop_event.set()
        # Show acknowledgment while the worker remains owned and active.
        self.update_status("Stop requested")

    # Provide detached data for the UI without dataclass indexing errors.
    def snapshot(self):
        """Return typed log compatibility plus explicitly serialized event dictionaries."""
        # Read all mutable monitoring fields under one lock.
        with self._lock:
            # Keep historical typed logs and a convenient UI-safe serialized view.
            return {"status": self.status, "logs": list(self.logs), "events": [asdict(event) for event in self.logs], "screenshots": list(self.screenshots), "waiting": dict(self.waiting), "stopped": self.stop_event.is_set()}
