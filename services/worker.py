"""Process-isolated execution and responsive Streamlit control channels.

One spawned worker owns one browser, selected provider, graph, and evidence store.
The parent UI receives safe compact events; API keys remain runtime-only and never
enter checkpoints or command-line arguments. Stop has a bounded cleanup boundary.
"""
# Use explicit spawn semantics compatible with Windows and Streamlit reruns.
import multiprocessing
# Drain event queues without blocking UI refreshes.
from queue import Empty
# Track Stop deadlines without a global task-duration limit.
import time
# Serialize only safe diagnostic events to the run's log artifact.
import json
# Convert typed event records across process boundaries.
from dataclasses import asdict
# Reference complete evidence artifacts rather than sending huge output through a queue.
from pathlib import Path
# Preserve the shared monitor contract and its redaction boundary.
from services.monitoring import RunMonitor
# Reconstruct typed parent-side events without dictionary-indexing dataclasses.
from domain.models import RunEvent
# Redact accidental secrets before writing diagnostics.
from domain.events import redact_secrets


# Forward live worker progress to the parent process.
class WorkerMonitor(RunMonitor):
    """Connect safe events, Stop, Pause, and explicit user responses to one worker."""

    # Keep multiprocessing synchronization primitives supplied by the parent.
    def __init__(self, events, responses, stop_event, pause_event):
        """Bind IPC channels without creating a second owner for browser resources."""
        # Initialize compatible local status and image bookkeeping.
        super().__init__()
        # Share the parent's actual Stop signal.
        self.stop_event = stop_event
        # Freeze automation between graph/browser operations when Pause is active.
        self.pause_event = pause_event
        # Send compact events to the one parent UI.
        self.events = events
        # Receive explicit authorization, assistance, or scope responses.
        self.responses = responses
        # Attach the log path after the adapter allocates its run directory.
        self.log_path = None
        # Record only processes started for this worker, never an older compatible browser.
        self.created_at = time.time()
        # The worker entry point assigns its validated managed profile before startup.
        self.profile_path = None

    # Publish concrete browser ownership before any potentially blocked model request.
    def record_browser_ownership(self):
        """Identify this run's profile-owned browser processes outside the UI thread."""
        # Use process metadata only to identify this worker's explicit managed profile.
        import psutil
        # No profile has been opened when runtime setup has not reached initialization.
        if self.profile_path is None:
            # Direct test monitors may omit managed-profile configuration.
            return
        # Normalize Windows paths without exposing cookie or login data.
        profile = str(self.profile_path).lower().replace("\\", "/")
        # Send only exact process identities and creation times.
        records = {}
        # Inspect the actual browser launch arguments before automatic task execution.
        for process in psutil.process_iter(["pid", "cmdline", "create_time"]):
            # Processes can exit during ordinary browser startup.
            try:
                # A pre-existing process is never captured by this run's cleanup authority.
                if process.info["create_time"] >= self.created_at - 1 and any(profile in argument.lower().replace("\\", "/") for argument in process.info["cmdline"] or []):
                    # Retain the proved profile owner and any renderer/helper descendants.
                    for owned in [process, *process.children(recursive=True)]:
                        # Creation time prevents PID reuse from targeting another application.
                        records[owned.pid] = {"pid": owned.pid, "created_at": owned.create_time()}
            # Unrelated inaccessible processes do not belong to this run.
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Continue without recording or displaying unrelated process metadata.
                continue
        # The parent receives only ownership proof, never full command lines.
        self._emit({"type": "ownership", "processes": list(records.values())})

    # Preserve safe diagnostics as well as their live UI stream.
    def _emit(self, payload):
        """Queue one event and append safe chronological diagnostic records to disk."""
        # Keep event delivery separate from potentially large source exports.
        self.events.put(payload)
        # Only safe diagnostic events are written to JSONL, not runtime control secrets.
        if self.log_path is not None and payload["type"] == "event":
            # Append without rewriting the entire run log each second.
            with self.log_path.open("a", encoding="utf-8") as stream:
                # Redact before persistence as well as before UI display.
                stream.write(redact_secrets(json.dumps(payload["event"], ensure_ascii=False)) + "\n")

    # Publish concise live status and its original worker timestamp.
    def update_status(self, status):
        """Update compatible local state and forward the source-timestamped event."""
        # Shared monitoring performs automatic redaction.
        super().update_status(status)
        # Forward one event rather than copying a growing log history.
        self._emit({"type": "event", "event": asdict(self.logs[-1]), "status": self.status})

    # Preserve meaningful safe error/warning diagnostics.
    def log(self, level, message):
        """Forward an actual diagnostic without leaking request bodies or keys."""
        # Use the common safe event constructor.
        super().log(level, message)
        # Preserve severity and timestamp across the process boundary.
        self._emit({"type": "event", "event": asdict(self.logs[-1])})

    # Stream immutable images as they are captured.
    def add_screenshot(self, path):
        """Publish a single image reference, retaining source order."""
        # Avoid duplicate event emission for an already recorded path.
        if path not in self.screenshots:
            # Maintain the compatible local capture inventory.
            super().add_screenshot(path)
            # Send a path, never base64 image contents.
            self._emit({"type": "screenshot", "path": path})

    # Freeze automatic execution for a concrete user-only decision.
    def request(self, request):
        """Forward a typed assistance/authorization request without claiming completion."""
        # Keep the local wait state consistent with the parent UI.
        super().request(request)
        # Empty requests explicitly clear the prior prompt after resumption.
        self._emit({"type": "waiting", "request": request})

    # Await a real response while honoring Stop.
    def await_response(self):
        """Return the user's concrete response or None after cancellation."""
        # No timeout may silently authorize a new host or authentication gate.
        while not self.stop_event.is_set():
            # Wait briefly so Stop remains responsive.
            try:
                # Consume only explicit UI responses.
                return self.responses.get(timeout=0.1)
            # A pending response is an ordinary waiting state.
            except Empty:
                # Keep waiting without dispatching browser input.
                continue
        # Cancellation ends assistance without fabricating approval.
        return None

    # Pause can stop local scrolling as well as graph-cycle boundaries.
    def gate(self):
        """Block automatic work during Pause; allow Resume or Stop promptly."""
        # Publish the paused state only when a pause is actually active.
        if self.pause_event.is_set():
            # Reuse assistance UI without consuming a future hostname response.
            self.request({"kind": "paused", "message": "Automation is paused."})
            # Keep all browser/model actions frozen until Resume.
            while self.pause_event.is_set() and not self.stop_event.is_set():
                # Check cancellation while waiting for the parent to clear Pause.
                self.stop_event.wait(0.1)
            # Clear the pause prompt before any automatic action resumes.
            self.request({})


# Spawn-safe entry point with no Streamlit imports or global browser launch.
def _worker_main(task, site, configuration, events, responses, stop_event, pause_event, provider_factory=None):
    """Construct runtime-only dependencies, execute the approved run, and publish its outcome."""
    # Import runtime factories only inside the worker process.
    from services.run_controller import create_provider, create_browser_adapter, execute_run
    # Bind current-run event and command channels.
    monitor = WorkerMonitor(events, responses, stop_event, pause_event)
    # Preserve terminal event delivery even when dependency setup fails.
    try:
        # Initialize exactly the selected executor.
        adapter = create_browser_adapter(configuration.browser_method)
        # Make the run's artifact directory available before the first model request.
        adapter._screenshot_dir.mkdir(parents=True, exist_ok=True)
        # Resolve the explicit managed profile before collecting any process ownership.
        from browser.session_manager import session_path
        # Ownership collection runs in this child, keeping Streamlit responsive.
        monitor.profile_path = session_path(site, configuration.browser_method).resolve()
        # Persist safe diagnostics next to the source evidence.
        monitor.log_path = adapter._screenshot_dir / "events.jsonl"
        # Publish only the run-owned directory for partial-result recovery.
        events.put({"type": "directory", "path": str(adapter._screenshot_dir)})
        # Construct only the active fixed model using its runtime credential.
        provider = (provider_factory or create_provider)(configuration.model_provider, configuration.api_key)
        # Execute checkpointed cycles and complete/partial source export.
        result = execute_run(task, site, configuration, adapter, provider, monitor)
        # Send compact lifecycle and artifact references, not credentials or giant transcripts.
        compact = {key: result.get(key) for key in ("finished", "verified", "stopped", "status", "blocker", "artifacts", "collected_pages")}
        # Preserve final outcome until the parent explicitly starts another run.
        events.put({"type": "result", "result": compact})
    # Setup failures must reach the UI even when graph execution never begins.
    except Exception as exc:
        # Keep a bounded actionable error without exposing provider input.
        message = type(exc).__name__ + ": " + redact_secrets(str(exc))[:500]
        # Publish an honest failure, not a stale active state.
        events.put({"type": "result", "result": {"finished": True, "verified": False, "blocker": message, "status": "Blocked"}})


# Parent-side owner that survives Streamlit reruns in session state.
class RunSupervisor:
    """Own one worker process, IPC channels, Stop deadline, and current UI monitor."""

    # Start one run only after UI configuration validation succeeds.
    def __init__(self, task, site, configuration, provider_factory=None):
        """Launch an isolated spawn worker; never store credentials in event artifacts."""
        # Reject invalid provider/method/key settings before process creation.
        configuration.validate()
        # Keep monitoring local to this application session.
        self.monitor = RunMonitor()
        # Use Windows-safe process creation rather than inherited UI threads.
        context = multiprocessing.get_context("spawn")
        # Send compact safe progress events from worker to parent.
        self.events = context.Queue()
        # Receive explicit human decisions in the worker.
        self.responses = context.Queue()
        # Share Stop across the graph, traversal, and active tools.
        self.stop_event = context.Event()
        # Pause freezes work without terminating the selected browser session.
        self.pause_event = context.Event()
        # Mirror the actual stop signal into the parent monitor.
        self.monitor.stop_event = self.stop_event
        # Allocate a deadline only after Stop is requested.
        self.stop_requested_at = None
        # Retain the run-owned evidence directory for forced-stop partial recovery.
        self.directory = None
        # Retain concrete detached-browser identities reported before model work begins.
        self.owned_processes = {}
        # Spawn a top-level target without importing/rerunning Streamlit in the child.
        self.process = context.Process(target=_worker_main, args=(task, site, configuration, self.events, self.responses, self.stop_event, self.pause_event, provider_factory), name="intelligent-browser-run", daemon=True)
        # Mark real worker ownership before starting, preventing duplicate UI starts.
        self.monitor.active = True
        # Start the child without any command-line API key.
        # Record the run start time so profile matching cannot capture an older unrelated process.
        self.launched_at = time.time()
        # Retain the explicit managed profile for detached-browser cleanup on Windows.
        from browser.session_manager import session_path
        # Site/method validation keeps the resolved profile under application-owned session storage.
        self.profile_path = session_path(site, configuration.browser_method).resolve()
        # Begin the worker only after its ownership boundary is recorded.
        self.process.start()

    # Receive progress without blocking Streamlit controls.
    def poll(self):
        """Drain available events and enforce bounded cancellation/abnormal-exit handling."""
        # Consume only currently available events during this refresh.
        while True:
            # Avoid a blocking queue read in the UI.
            try:
                # Each message is a compact typed event.
                event = self.events.get_nowait()
            # Nothing more is available this refresh.
            except Empty:
                # Return to responsive rendering.
                break
            # Preserve source event timestamps and safe severity.
            if event["type"] == "event":
                # Reconstruct a typed record without dictionary-indexing it later.
                self.monitor.logs.append(RunEvent(**event["event"]))
                # Keep the UI's recent window bounded while JSONL retains full history.
                self.monitor.logs = self.monitor.logs[-1000:]
                # Status events also update the concise current activity.
                if "status" in event:
                    # Retain the already redacted current status.
                    self.monitor.status = event["status"]
            # Stream immutable screenshot references.
            elif event["type"] == "screenshot":
                # Preserve the compatible parent monitor's deduplication.
                self.monitor.add_screenshot(event["path"])
            # Assistance is an actual wait state, not an inactive/finished worker.
            elif event["type"] == "waiting":
                # Keep requests available until the user responds.
                self.monitor.waiting = event["request"]
                # Concise lifecycle status must agree with the actual user-only wait.
                self.monitor.status = "Waiting: " + event["request"]["kind"] if event["request"] else "Resuming"
            # Track only the current run's artifact directory.
            elif event["type"] == "directory":
                # Preserve source evidence for abnormal-stop recovery.
                self.directory = Path(event["path"])
            # Retain proved detached-browser identities independently of worker ancestry.
            elif event["type"] == "ownership":
                # Keep all browser generations opened by assistance visibility transfers.
                self.owned_processes.update({item["pid"]: item["created_at"] for item in event["processes"]})
            # Terminal results explicitly release active-run UI ownership.
            elif event["type"] == "result":
                # Preserve lifecycle and complete/partial artifact references.
                self.monitor.result = event["result"]
                # Do not permit another Start until the owned process has actually exited.
                self.monitor.status = event["result"].get("status", "Finished")
        # Enforce a bounded cleanup deadline after Stop.
        if self.stop_requested_at is not None and self.process.is_alive() and time.monotonic() - self.stop_requested_at > 5:
            # Stop only this worker and the descendant processes it owns.
            self._terminate_owned_tree()
        # Process death without a terminal event must not leave the UI permanently running.
        if not self.process.is_alive():
            # Reap the owned child without waiting for another browser task.
            self.process.join(timeout=0)
            # Retain honest partial state if the worker could not send its final result.
            if self.monitor.result is None:
                # Recover committed source records even after forced termination before normal export.
                if self.directory and (self.directory / "evidence.sqlite3").is_file():
                    # Reopen only the dead worker's own evidence database.
                    from services.evidence import EvidenceStore
                    # No live writer remains after actual process exit.
                    recovered = EvidenceStore(self.directory)
                    # Preserve complete committed blocks and mark the outcome partial below.
                    recovered.export()
                    # Release the recovered database before rendering downloads.
                    recovered.close()
                # Existing files remain inspectable after a crash or forced cancellation.
                artifacts = {name: str(self.directory / filename) for name, filename in (("text", "result.txt"), ("markdown", "result.md"), ("manifest", "manifest.json")) if self.directory and (self.directory / filename).exists()}
                # Distinguish Stop from an unexpected runtime exit.
                self.monitor.result = {"finished": True, "verified": False, "stopped": self.stop_event.is_set(), "status": "Stopped" if self.stop_event.is_set() else "Blocked", "blocker": "Worker stopped before normal finalization; available artifacts are partial.", "artifacts": artifacts}
            # Re-enable configuration only after actual process exit.
            self.monitor.active = False
        # Return the consistent current-run state to the UI.
        return self.monitor

    # Request responsive cancellation while preserving a short normal-cleanup opportunity.
    def stop(self):
        """Set Stop and begin a five-second owned-process cleanup deadline."""
        # Signal graph and local browser operations immediately.
        self.stop_event.set()
        # Stop overrides a user pause.
        self.pause_event.clear()
        # Record only the first Stop deadline.
        self.stop_requested_at = self.stop_requested_at or time.monotonic()
        # Show acknowledgement without falsely claiming resources already stopped.
        self.monitor.update_status("Stop requested; cleaning up owned browser")

    # Pause before the next browser or model operation.
    def pause(self):
        """Freeze automatic work while retaining the selected browser and task state."""
        # A completed worker cannot be paused.
        if self.process.is_alive():
            # The worker checks this inside traversal and at node boundaries.
            self.pause_event.set()

    # Resume only after a concrete user decision.
    def respond(self, response):
        """Send an explicit assistance/authorization response or clear an ordinary Pause."""
        # Paused runs do not consume a later authentication/hostname response.
        if self.monitor.waiting.get("kind") == "paused":
            # Let the worker's gate return without queueing a stale approval.
            self.pause_event.clear()
        # Other waiting states require a concrete command payload.
        else:
            # No preselected option or elapsed time creates this response automatically.
            self.responses.put(dict(response))
        # The worker re-observes before resuming browser actions.
        self.monitor.waiting = {}

    # Terminate only processes owned by this run after graceful Stop failed.
    def _terminate_owned_tree(self):
        """Bound cancellation without global browser kills or deletion of session profiles."""
        # Inspect descendants before terminating their owning worker.
        try:
            # psutil is a declared dependency used only for scoped lifecycle cleanup.
            import psutil
            # Retain actual descendants rather than matching all Chrome process names.
            children = psutil.Process(self.process.pid).children(recursive=True)
            # Detached daemons retain identities recorded by the worker before model requests.
            owned = {child.pid: child for child in children}
            # Resolve only those proved PID/creation-time pairs, avoiding a blocking global inventory.
            for pid, created_at in self.owned_processes.items():
                # Ordinary process exit or PID reuse must not target another application.
                try:
                    # psutil checks this concrete process identity before termination.
                    candidate = psutil.Process(pid)
                    # Require its original creation time before adding it to scoped cleanup.
                    if abs(candidate.create_time() - created_at) < 0.01:
                        # Include still-live renderer/helper children created after the initial report.
                        owned[candidate.pid] = candidate
                        # Retain only descendants of that proved owned browser.
                        owned.update({child.pid: child for child in candidate.children(recursive=True)})
                # A previously closed browser generation needs no cleanup.
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Continue with other proved process identities.
                    continue
            # Request termination from deepest owned children first.
            children = list(owned.values())
            # Terminate only the proved owned inventory from deepest discovered processes first.
            for child in reversed(children):
                # Ignore processes that exited during normal cleanup.
                try:
                    # Terminate only this concrete descendant PID.
                    child.terminate()
                # Races with process exit are normal during cancellation.
                except psutil.Error:
                    # Continue cleaning other owned resources.
                    pass
            # Reap terminated descendants before declaring the task stopped.
            gone, alive = psutil.wait_procs(children, timeout=0.5)
            # A surviving owned child must not keep an abandoned browser active.
            for child in alive:
                # PID reuse or normal exit races are handled by psutil's identity checks.
                try:
                    # Escalate only this previously proved owned process.
                    child.kill()
                # Exit races do not authorize touching another process.
                except psutil.Error:
                    # Continue completing the remaining scoped cleanup.
                    pass
        # A process that already exited needs no further action.
        except Exception as exc:
            # Worker termination below remains bounded even without descendant inventory.
            self.monitor.log("WARNING", "Owned-process inspection failed: " + type(exc).__name__)
        # Stop the owned worker, never unrelated user applications.
        self.process.terminate()
        # Reap it within a bounded wait.
        self.process.join(timeout=1)
