"""Coordinate checkpointed LangGraph cycles and selected runtime dependencies.

This module owns task lifecycle, source exports, assistance, and clean terminal
outcomes. The UI supervisor runs it in an isolated process; runtime handles and
provider credentials never enter serialized graph checkpoints.
"""
# Serialize only explicit graph state and source manifest paths.
import json
# Preserve data-record compatibility for injected model/browser tests.
from pathlib import Path
# Authorize exact hostnames after explicit user decisions.
from urllib.parse import urlparse
# Allocate fallback artifacts for injected test adapters without runtime handles.
from uuid import uuid4
# Select the two approved fixed-model transports.
from models.gemini_provider import GeminiProvider
# Keep the correctly named Groq Qwen provider distinct from xAI Grok.
from models.groq_provider import GroqProvider
# Select exactly one actual browser executor.
from browser.playwright_mcp import PlaywrightMCPAdapter
# Preserve CLI as a real independent executor.
from browser.playwright_cli import PlaywrightCLIAdapter
# Keep Browser Use under shared LangGraph reasoning rather than a second agent.
from browser.browser_use import BrowserUseAdapter
# Compile real LangGraph cycles without an arbitrary total step cutoff.
from agent.graph import build_graph
# Preserve complete source outside bounded model observations.
from services.evidence import EvidenceStore
# Keep specific safe failures in user-visible diagnostics.
from domain.events import redact_secrets
# Route authorization and human-only conditions separately from task success.
from domain.errors import AuthorizationRequired
# Compare revisits and evidence through canonical content identities.
from services.identity import canonical_url


# Construct only the selected model client.
def create_provider(provider_name, api_key):
    """Return the fixed Gemini or Groq transport; reject incorrectly labeled providers."""
    # Keep provider labels and actual endpoints aligned.
    if provider_name == "gemini":
        # No Groq client is created when Gemini is active.
        return GeminiProvider(api_key)
    # The approved second provider is Groq, not xAI Grok.
    if provider_name == "groq":
        # Qwen handles both screenshot input and reasoning.
        return GroqProvider(api_key)
    # Do not silently accept a stale provider identifier.
    raise ValueError("Unsupported model provider; choose Gemini or Groq.")


# Construct exactly the selected browser method.
def create_browser_adapter(method, **dependencies):
    """Return one actual transport with explicit optional test injection."""
    # Keep deterministic injected controllers separate from live defaults.
    if method == "playwright_mcp":
        # Live execution uses the pinned MCP server.
        return PlaywrightMCPAdapter(client=dependencies.get("mcp_client"))
    # CLI remains a real CLI method rather than an alias for Python Playwright.
    if method == "playwright_cli":
        # Tests may override the executable without changing method selection.
        return PlaywrightCLIAdapter(command=dependencies.get("cli_command"))
    # Browser Use stays a low-level executor under the shared LangGraph agent.
    if method == "browser_use":
        # No independent Browser Use agent or model is initialized.
        return BrowserUseAdapter(controller=dependencies.get("browser_use_controller"))
    # Unsupported methods must fail visibly.
    raise ValueError("Unsupported browser method.")


# Pause a logical run for authorization or genuine human assistance.
def _assist(state, adapter, monitor):
    """Wait for a concrete UI response, preserving the run and eligible browser session."""
    # Copy the actual pending condition.
    request = dict(state["waiting"])
    # Authentication or verification may require moving a headless session to a visible browser.
    transfer = request["kind"] in {"login", "captcha", "assistance"} and not state.get("headful")
    # Preserve the exact selected site for profile isolation and policy.
    original_site = state["selected_site"]
    # Restore the current permitted destination after a visibility transition.
    current_url = state.get("observation", {}).get("url", original_site)
    # Make an interactive browser available before asking the user to solve the step.
    if transfer:
        # Capture session cookies/storage in memory before the browser runtime shuts down.
        adapter.prepare_transfer()
        # Close only the owned headless browser, retaining eligible session data.
        adapter.close_or_detach()
        # Reapply explicit grants after recreating the selected runtime.
        adapter.set_site(original_site, True, state.get("authorized_external_domains", []))
        # Reopen the same logical website/method session visibly.
        adapter.initialize(original_site, True)
        # Publish this new browser generation before waiting or reasoning can block.
        if hasattr(monitor, "record_browser_ownership"):
            # Ownership metadata remains outside checkpointed task state.
            monitor.record_browser_ownership()
        # Restore a permitted in-progress location when it differs from the landing page.
        if current_url != original_site and adapter.is_allowed_url(current_url):
            # Re-navigation is explicit; transient in-memory page state may need recreation.
            adapter._native("navigate", current_url)
        # Inform the UI that the assistance session is currently visible.
        state["headful"] = True
    # Publish a typed waiting prompt rather than claiming a completed task.
    monitor.request(request)
    # No direct synchronous test or missing UI may automatically approve a host.
    response = monitor.await_response()
    # Stop or refusal must retain partial source and end honestly.
    if not response or response.get("action") == "deny" or monitor.stop_event.is_set():
        # Surface the unresolved condition separately from captured source text.
        state.update({"finished": True, "verified": False, "blocker": "User assistance was not completed: " + request["kind"], "waiting": {}})
        # Prevent automatic input from resuming.
        return
    # An exact-host grant is explicit and applies only to this run.
    if request["kind"] == "hostname":
        # Preserve only the requested destination's actual hostname.
        host = (urlparse(request["url"]).hostname or "").lower()
        # Add this concrete grant rather than permitting all subdomains.
        state["authorized_external_domains"] = list(dict.fromkeys([*state.get("authorized_external_domains", []), host]))
        # Update the common adapter policy.
        adapter.set_site(original_site, state.get("headful", False), state["authorized_external_domains"])
        # Retry the explicitly authorized proposed destination.
        adapter._native("navigate", request["url"])
    # Potentially non-finite feeds require a positive explicit bound.
    if request["kind"] == "scope_limit":
        # Reject empty or nonsensical criteria rather than silently assuming a limit.
        limit = int(response.get("limit", 0))
        # Keep the criterion meaningful for the current page traversal.
        if limit <= 0:
            # A missing criterion is still a genuine scope blocker.
            raise ValueError("A positive traversal-action limit is required")
        # Preserve the user-defined bound in checkpoint state.
        state["scroll_limit"] = limit
    # Clear a stale assistance prompt only after the concrete response was applied.
    monitor.request({})
    # Force a new observation of the user's actual resulting browser state.
    state.update({"waiting": {}, "last_error": "", "observation_ready": False, "attempts": 0})
    # Restore headless mode after user assistance when that was the original preference.
    if transfer:
        # Capture the actual allowed location after the user completed the step.
        current_url = adapter.probe()["url"]
        # Preserve authentication cookies/storage without relying on a browser disk flush.
        adapter.prepare_transfer()
        # Persist eligible authentication state through normal selected-method cleanup.
        adapter.close_or_detach()
        # Keep the original hostname/profile boundary.
        adapter.set_site(original_site, False, state["authorized_external_domains"])
        # Reopen the same compatible session without a visible window.
        adapter.initialize(original_site, False)
        # Keep restored browser ownership available for prompt Stop.
        if hasattr(monitor, "record_browser_ownership"):
            # Record exact process identities in the worker rather than blocking the UI.
            monitor.record_browser_ownership()
        # Restore the user's actual post-authentication destination if permitted.
        adapter._native("navigate", current_url)
        # Reflect the restored user-selected mode.
        state["headful"] = False


# Detect repeated navigation without treating new URLs alone as task evidence.
def navigation_cycle(state, previous_url, seen):
    """Return True on a third revisit without new captured/reviewed/frontier progress."""
    # Scope repeat counts to current evidence and relevance-review progress.
    epoch = (len(state.get("visited", [])), len(state.get("reviewed_links", [])), tuple(state.get("frontier", [])), hash(state.get("output", "")))
    # Fresh evidence or a deliberate frontier revision permits legitimate future revisits.
    if seen.get("epoch") != epoch:
        # Discard stale counts after meaningful task progress.
        seen.clear()
        # Preserve the evidence boundary alongside URL counts.
        seen["epoch"] = epoch
    # Read the independently observed result of this cycle.
    current = canonical_url(state.get("observation", {}).get("url", ""))
    # Normalize the previous destination through the same content identity rules.
    previous_url = canonical_url(previous_url)
    # Scrolls and local filters are not cross-page navigation loops.
    if current and previous_url and current != previous_url and state.get("decision", {}).get("kind") in {"navigate", "click", "press"}:
        # Count revisits only within unchanged task evidence.
        seen[current] = seen.get(current, 0) + 1
        # Repeated arrivals without evidence establish a navigation cycle.
        return seen[current] >= 3
    # Ordinary exploration and source collection remain unrestricted.
    return False


# Run one task using real bounded graph cycles and a durable evidence store.
def execute_run(task, site, configuration, adapter, provider, monitor, external_domains=None):
    """Return honest terminal state and complete/partial artifact paths; always clean owned resources."""
    # Reject invalid setup before opening the browser.
    configuration.validate()
    # Use the adapter's run-owned artifacts when available.
    directory = getattr(adapter, "_screenshot_dir", Path("data/run_artifacts") / uuid4().hex)
    # Preserve raw UI evidence independently of provider output tokens.
    store = EvidenceStore(directory)
    # Start with explicit serializable state; never put API keys or clients here.
    state = {"task": task, "selected_site": site, "authorized_external_domains": external_domains or [], "model_provider": configuration.model_provider, "browser_method": configuration.browser_method, "headful": configuration.headful, "history": [], "attempts": 0, "last_error": "", "screenshots": [], "output": "", "blocker": "", "verified": False, "finished": False, "waiting": {}, "visited": [], "collected_pages": {}, "frontier": [], "discovered_links": [], "reviewed_links": [], "goal": {}, "plan": [], "progress": {}, "action_memory": []}
    # Bind nonserializable dependencies only to the ephemeral graph runtime.
    context = {"adapter": adapter, "provider": provider, "monitor": monitor, "stop_event": monitor.stop_event, "store": store}
    # Preserve cleanup and partial export even if startup or orchestration fails.
    try:
        # Publish setup work before browser launch.
        monitor.update_status("Initializing selected browser session")
        # Share cancellation inside every local traversal and browser request.
        adapter.stop_event = monitor.stop_event
        # Publish images and source progress while execution is active.
        adapter.monitor = monitor
        # Keep initial authorization grants before adapter initialization.
        adapter.set_site(site, configuration.headful, external_domains or [])
        # An initial redirect may need explicit hostname permission.
        try:
            # Initialize exactly the selected execution method.
            adapter.initialize(site, configuration.headful, site + "::" + configuration.browser_method)
        # Preserve the proposed destination rather than returning a generic setup failure.
        except AuthorizationRequired as exc:
            # Keep startup authorization within the same resumable run.
            state["waiting"] = {"kind": "hostname", "url": exc.url}
            # Apply a concrete response before invoking the first graph cycle.
            _assist(state, adapter, monitor)
        # Record detached browser ownership before the first potentially blocked model request.
        if hasattr(monitor, "record_browser_ownership"):
            # The parent later terminates only these proved PID/creation-time identities.
            monitor.record_browser_ownership()
        # Compile real LangGraph once, reusing it for every checkpointed cycle.
        graph = build_graph()
        # Track revisits independently of browser transport success.
        navigation_seen = {}
        # Continue without a hidden global time/step limit.
        while not state.get("finished") and not monitor.stop_event.is_set():
            # User Pause freezes before another cycle/model call.
            if hasattr(monitor, "gate"):
                # The worker monitor makes this wait cancellable.
                monitor.gate()
            # Compare meaningful progress, not model prose or cursor animations.
            before = (state.get("observation", {}).get("fingerprint"), len(state.get("visited", [])), len(state.get("reviewed_links", [])), len(state.get("history", [])))
            # Retain the prior actual destination for cycle detection.
            previous_url = state.get("observation", {}).get("url", "")
            # Run a bounded cycle, not an unbounded monolithic graph invocation.
            state = graph.invoke(state, {"recursion_limit": 12}, context=context)
            # Collection/link review and real UI changes are actual task progress.
            after = (state.get("observation", {}).get("fingerprint"), len(state.get("visited", [])), len(state.get("reviewed_links", [])), len(state.get("history", [])))
            # Repeated URL changes without new source or scope progress cannot run forever.
            if navigation_cycle(state, previous_url, navigation_seen):
                # Preserve source and explain the concrete incomplete outcome.
                state.update({"finished":True,"verified":False,"blocker":"Repeated navigation revisited the same pages without new source or relevance progress.","status":"Partial: navigation loop detected"})
            # Repeated empty collect/finish/wait cycles must not run forever.
            state["stagnant"] = state.get("stagnant", 0) + 1 if before[:3] == after[:3] and state.get("last_outcome", {}).get("action") in {"wait", "collect"} else 0
            # A stalled run preserves partial evidence instead of claiming progress.
            if state["stagnant"] >= 5:
                # There is no fixed total step/time cap; only repeated no-progress is blocked.
                state.update({"finished": True, "verified": False, "blocker": "Repeated cycles made no observable task progress.", "status": "Partial or blocked"})
            # Preserve only JSON-safe state, not runtime credentials or browser handles.
            (store.directory / "checkpoint.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            # Handle genuine human-only decisions outside automatic browser input.
            if state.get("waiting"):
                # Resume always forces a new actual observation.
                _assist(state, adapter, monitor)
        # Cancellation is distinct from verified completion.
        if monitor.stop_event.is_set():
            # Preserve partial source and mark the run terminal.
            state.update({"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"})
    # A local traversal may observe Stop while inside a browser call.
    except InterruptedError:
        # Do not label cancellation as task success.
        state.update({"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"})
    # Setup, graph, and browser errors retain useful safe diagnostics.
    except Exception as exc:
        # Redact before logging or returning diagnostics.
        message = type(exc).__name__ + ": " + redact_secrets(str(exc))[:500]
        # Preserve the concrete cause for debugging.
        monitor.log("ERROR", message)
        # Keep partial information instead of swallowing the primary failure.
        state.update({"finished": True, "verified": False, "blocker": message, "status": "Partial or blocked"})
    # Export and cleanup occur for success, failure, stop, and abandoned assistance.
    finally:
        # Commit complete captured source regardless of the final lifecycle outcome.
        state["artifacts"] = store.export(state.get("goal"))
        # Keep the exact collected text, never model-generated replacement prose.
        state["output"] = store.text(state.get("goal"))
        # Close only the selected run's browser/profile runtime.
        try:
            # Adapters preserve reusable session data during normal cleanup.
            adapter.close_or_detach()
        # Cleanup diagnostics must not replace the original task result.
        except Exception as exc:
            # Keep the failure actionable and credential-safe.
            monitor.log("WARNING", "Browser cleanup: " + type(exc).__name__)
        # Release the worker-owned database after final exports.
        store.close()
    # Mirror the honest terminal outcome into monitoring.
    monitor.update_status(state.get("status", "Run finished"))
    # Return serializable state and artifact references.
    return state
