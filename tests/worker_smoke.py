"""Exercise actual spawned worker lifecycle with real browsers and local chapters.

The model is explicitly deterministic, so these tests do not claim live API success.
They prove process ownership, exact multi-page extraction, cycle avoidance, and Stop.
"""
# Resolve project imports for direct execution.
import sys
from pathlib import Path
# Serve only deterministic local source fixtures.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Avoid changing the process-wide working directory.
from functools import partial
# Run the controlled HTTP service alongside the owned worker.
from threading import Thread
# Measure real bounded cleanup and wait without busy polling.
import time
# Read independent coverage evidence after the worker exits.
import json
# Resolve root modules for Windows spawn-safe imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Validate the same configuration the UI submits.
from config.settings import RunConfiguration
# Exercise the actual supervisor and command/event queues.
from services.worker import RunSupervisor
# Keep fake model factories top-level and picklable.
from tests.worker_helpers import controlled_provider, slow_provider, noisy_review_provider


# Verify one actual selected executor inside an owned child process.
def main():
    """Complete two linked chapters or stop an in-flight simulated model call."""
    # Use the selected actual browser method, defaulting to Browser Use.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Bind a private local fixture origin.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Keep HTTP responses available while the worker owns browser execution.
    Thread(target=server.serve_forever, daemon=True).start()
    # Choose the explicit lifecycle scenario, never a hidden production-mode switch.
    stopping = "--stop" in sys.argv
    # No actual provider key is used or requested.
    configuration = RunConfiguration("gemini", method, False, "nonsecret-test-marker")
    # Dependency injection affects only the fake provider; browser, collector, and graph remain real.
    # Preserve the exact private origin for process-ownership verification.
    site = f"http://127.0.0.1:{server.server_port}/chapter_a.html"
    # Start the real worker with only its model collaborator replaced.
    supervisor = RunSupervisor("Retrieve both tutorial chapters exactly", site, configuration, provider_factory=slow_provider if stopping else noisy_review_provider if "--noisy-review" in sys.argv else controlled_provider)
    # Keep termination bounded if a test assertion fails.
    try:
        # Allow browser startup and collection without an arbitrary application task limit.
        deadline = time.monotonic() + 90
        # Track the actual Stop acknowledgment time.
        stopped_at = None
        # Observe real worker events and process ownership.
        while time.monotonic() < deadline:
            # Parent polling must remain nonblocking.
            monitor = supervisor.poll()
            # Stop only after the worker actually entered its fake model call.
            if stopping and stopped_at is None and "Choosing a grounded action" in monitor.status:
                # Signal cancellation while the simulated API call is still blocked.
                stopped_at = time.monotonic()
                # Begin bounded graceful/forced cleanup of only owned resources.
                supervisor.stop()
            # Real process exit, not a UI flag, ends run ownership.
            if not monitor.active:
                # Source artifacts are now stable for assertions.
                break
            # Keep polling light while actual browser work proceeds.
            time.sleep(0.05)
        # No worker may be left silently active after the diagnostic deadline.
        assert not supervisor.monitor.active, supervisor.monitor.status
        # Read the actual terminal outcome.
        result = supervisor.monitor.result
        # Cancellation cannot be reported as verified completion.
        if stopping:
            # Verify the run stopped while the simulated provider was still blocked.
            assert result.get("stopped") and not result.get("verified"), result
            # Measure actual stop completion before the independent process audit adds its own cost.
            stop_seconds = time.monotonic() - stopped_at
            # Verify cancellation also releases the actual browser, not just its worker flag.
            import psutil
            # Resolve only this fixture's isolated exact-host/method profile.
            from browser.session_manager import session_path
            # Match concrete command-line profile arguments without printing unrelated processes.
            profile = str(session_path(site, method)).lower().replace("\\", "/")
            # Keep a browser left behind by a detached CLI daemon from passing unnoticed.
            survivors = []
            # Inspect local process metadata only for this application's explicit owned profile.
            for process in psutil.process_iter(["pid", "cmdline"]):
                # Processes may exit while browser cleanup is finishing.
                try:
                    # Record only PIDs with this exact unique test profile argument.
                    if any(profile in argument.lower().replace("\\", "/") for argument in process.info["cmdline"] or []):
                        # No credentials or unrelated process details enter test output.
                        survivors.append(process.pid)
                # An inaccessible unrelated process is outside this owned test.
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Continue checking the actual owned profile.
                    continue
            # A worker-only stop is insufficient when the selected browser remains running.
            assert not survivors, {"owned_browser_pids_remaining": survivors, "method": method}
            # UI refresh plus bounded cleanup must beat the fake model's twenty-second delay.
            assert stop_seconds < 12, {"stop_seconds": stop_seconds, "result": result}
        # Normal completion needs exact independent source evidence.
        else:
            # The real graph must establish complete source coverage.
            assert result.get("verified"), result
            # Read the entire actual output artifact, not an IPC summary.
            text = Path(result["artifacts"]["text"]).read_text(encoding="utf-8")
            # Both chapters' original wording must appear once.
            assert text.count("Original first chapter: ₹1,299.00.") == 1, text
            # The relevant-link frontier must reach the second page.
            assert text.count("Original second chapter: unchanged wording.") == 1, text
            # A backlink must not create an infinite crawl or duplicate capture.
            manifest = json.loads(Path(result["artifacts"]["manifest"]).read_text(encoding="utf-8"))
            # Finite coverage is explicit and independently inspectable.
            assert len(manifest["pages"]) == 2 and all(page["complete"] for page in manifest["pages"]), manifest["pages"]
        # Keep lifecycle proof compact and credential-free.
        print({"method": method, "scenario": "blocked-call-stop" if stopping else "linked-page-worker", "verified": result.get("verified"), "stopped": result.get("stopped", False), "status": result.get("status"), "artifacts": result.get("artifacts")})
    # Ensure a failed assertion does not leave an owned browser worker running.
    finally:
        # Only this explicit supervisor's resources may be terminated.
        if supervisor.process.is_alive():
            # Enforce the same bounded Stop path as the actual UI.
            supervisor.stop()
            # Complete scoped cleanup after the diagnostic failure.
            supervisor._terminate_owned_tree()
        # Stop the private local HTTP fixture.
        server.shutdown()
        # Release its socket for repeated independent tests.
        server.server_close()


# Windows spawn must not rerun the test harness in the child process.
if __name__ == "__main__":
    # Launch only from this explicit diagnostic entry point.
    main()
