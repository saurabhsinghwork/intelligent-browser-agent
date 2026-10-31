"""Browser Use low-level transport under the shared LangGraph decision maker.

Actual Browser Use Page/Element APIs dispatch native input. A dedicated event loop
owns the selected session; Boolean strings and base64 screenshots are normalized.
"""
# Bridge asynchronous Browser Use APIs to synchronous graph nodes.
import asyncio
# Decode viewport PNGs returned by the installed Browser Use screenshot API.
import base64
# Encode stable selectors and normalize structured page results.
import json
# Keep one event-loop thread and bounded cancellable future waits.
from threading import Thread
# Poll coroutine completion with short waits so Stop remains responsive.
from concurrent.futures import TimeoutError as FutureTimeout
# Bound individual operations independently of overall task length.
import time
# Give only this executor's browser subprocesses the actual interactive Windows desktop.
from browser.windows_desktop import browser_launch_options, browser_command, require_visible_browser
# Normalize redirect destinations before exact-host authorization.
from urllib.parse import urljoin, urlparse
# Share observation, policy, scrolling, and result validation.
from browser.base import BaseBrowserAdapter, decode_result
# Reuse isolated persistent session directories.
from browser.session_manager import ensure_session_dir
# Use the same installed Google Chrome as the CLI/MCP executors.
from browser.chrome_runtime import installed_chrome
# Report concrete authorization requests without treating them as task success.
from domain.errors import AuthorizationRequired


# Implement Browser Use as an executor, not an independent autonomous agent.
class BrowserUseAdapter(BaseBrowserAdapter):
    """Own one Browser Use session and actual element identities for the selected run."""

    # Do not allocate an event-loop thread until a live browser is actually required.
    def __init__(self, controller=None):
        """Store optional injected controller and empty live session state."""
        # Initialize shared exact-host policy and unique artifact paths.
        super().__init__()
        # Retain controller injection for deterministic contract tests.
        self.controller = controller
        # Keep live runtime objects outside graph checkpoints.
        self._browser = None
        # Track the actual active Browser Use actor page.
        self._page = None
        # Allocate asynchronous infrastructure lazily.
        self._loop = None
        # Join the owned event-loop thread during cleanup.
        self._thread = None
        # Permit bounded cleanup after Stop without clearing the shared stop signal.
        self._closing = False
        # Retain a denied URL for explicit hostname authorization.
        self._blocked_url = ""
        # Keep every intercepted page session under the same exact-host policy.
        self._guarded_sessions = {}
        # Distinguish the selected actor page from attached popup page sessions.
        self._primary_sessions = set()
        # Remember child pages created during a concrete agent click for a short bounded interval.
        self._intent_sessions = set()
        # Retain target identities so unsolicited external popup pages can be closed.
        self._guarded_targets = {}
        # Do not attribute background advertising targets to a stale user gesture.
        self._navigation_intent_deadline = 0.0
        # Install root popup interception once without replacing the runtime's own handler.
        self._popup_guard_installed = False

    # Mark the short interval in which an agent click may intentionally create a page.
    def _begin_navigation_intent(self, seconds=2.0):
        """Permit a just-clicked popup to request authorization without trusting later ads."""
        # Use the caller's small bounded interval without leaking intent into later page activity.
        self._navigation_intent_deadline = time.monotonic() + seconds

    # Classify only verified active-page or current-click destinations as user-facing navigation.
    def _should_request_hostname(self, session_id):
        """Return whether an unauthorized document belongs to an agent-directed page."""
        # The selected actor page may navigate externally only during a concrete agent action.
        if session_id in self._primary_sessions:
            # Refuse delayed script redirects that are not caused by current agent intent.
            return time.monotonic() <= self._navigation_intent_deadline
        # A child page must both belong to and still be inside the current concrete click interval.
        return session_id in self._intent_sessions and time.monotonic() <= self._navigation_intent_deadline

    # Register one attached page without assuming every page target is user-directed.
    def _register_attached_page(self, session_id, target_id):
        """Track a guarded child page and bind it only to a current click interval."""
        # The first document request will establish this new page's main frame.
        self._guarded_sessions[session_id] = None
        # Retain the exact target for scoped cleanup if it proves unsolicited.
        self._guarded_targets[session_id] = target_id or ""
        # Browser Use may expose the selected actor through an attached child CDP session.
        active_target = getattr(self._page, "_target_id", "") if self._page is not None else ""
        # Treat every protocol session for the active actor as genuine top-level navigation.
        if target_id and target_id == active_target:
            # Preserve hostname handoff for redirects regardless of runtime session topology.
            self._primary_sessions.add(session_id)
            # Active-page identity is stronger evidence than the short click interval.
            return
        # A recent concrete click is the only source of child-page navigation intent.
        if time.monotonic() <= self._navigation_intent_deadline:
            # Grant prompt eligibility to this child session rather than all future targets.
            self._intent_sessions.add(session_id)

    # Store only genuine user-facing hostname transitions for the Streamlit handoff.
    def _record_denied_destination(self, session_id, destination):
        """Record an unauthorized destination only when navigation intent is verified."""
        # Incidental advertising targets are blocked without creating an authorization prompt.
        if not self._should_request_hostname(session_id):
            # Tell the interceptor to clean up this unsolicited target silently.
            return False
        # Preserve the concrete destination for the run-scoped approval UI.
        self._blocked_url = destination
        # Tell the interceptor that this is a genuine user-facing boundary.
        return True

    # Await one Browser Use coroutine with responsive cancellation.
    def _await(self, coroutine):
        """Return a coroutine result or cancel on Stop/deadline; never leave timed-out work running."""
        # Submit work to the loop that owns browser objects.
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        # Bound only this operation, not the complete research task.
        deadline = time.monotonic() + 30
        # Poll completion while preserving cancellation responsiveness.
        while time.monotonic() < deadline:
            # Prevent input from continuing after the user presses Stop.
            if not self._closing and self.stop_event.is_set():
                # Cancel the actual asynchronous browser operation.
                future.cancel()
                # Let the supervisor preserve evidence and terminate owned resources.
                raise InterruptedError("Stopped during Browser Use operation")
            # Wait briefly for a result.
            try:
                # A short future wait allows repeated Stop checks.
                return future.result(timeout=0.1)
            # The browser may still be navigating or initializing.
            except FutureTimeout:
                # Continue until this operation's deadline or Stop.
                continue
        # Cancel instead of letting timed-out work mutate the browser later.
        future.cancel()
        # Report a meaningful bounded operation failure.
        raise TimeoutError("Browser Use operation timed out")

    # Guard requests and redirects before their destination is committed.
    async def _install_guard(self):
        """Intercept document requests through the CDP client owned by Browser Use."""
        # Obtain the actor's supported CDP session identity.
        session = await self._page.session_id
        # Use the Browser Use session's client instead of attaching another automation engine.
        client = self._browser.cdp_client
        # Keep this session identity for element resolution and browser-level input.
        self._session_id = session
        # Distinguish main-frame browsing from ordinary embedded document resources.
        tree = await client.send.Page.getFrameTree(session_id=session)
        # Third-party resources do not grant permission for top-level navigation.
        self._main_frame_id = tree["frameTree"]["frame"]["id"]
        # Retain frame identity by session so newly opened pages can be guarded too.
        self._guarded_sessions[session] = self._main_frame_id
        # Associate this root session with the selected actor's stable target identity.
        self._guarded_targets[session] = self._page._target_id
        # Retain every protocol session that belongs to the selected actor target.
        self._primary_sessions = {session_id for session_id, target_id in self._guarded_targets.items() if target_id == self._page._target_id}
        # The actor's current root session always represents ordinary top-level browsing.
        self._primary_sessions.add(session)

        # Handle intercepted document navigation using the exact current hostname grants.
        async def handle_paused(event, session_id):
            """Continue authorized documents or fail forbidden requests before network access."""
            # Ignore unrelated sessions handled by the browser runtime.
            if session_id not in self._guarded_sessions:
                # The registered handler is enabled only for the active page.
                return
            # Read the actual requested URL, including redirected requests.
            destination = event["request"]["url"]
            # Embedded frames may load as website resources without authorizing agent navigation.
            if self._guarded_sessions[session_id] is None:
                # The first document request of a paused new page identifies its main frame.
                self._guarded_sessions[session_id] = event.get("frameId")
            # Embedded documents remain resources, not top-level browsing permission.
            if event.get("frameId") != self._guarded_sessions[session_id]:
                # Automated inspection of a different-host frame still needs its own support/policy.
                await client.send.Fetch.continueRequest({"requestId": event["requestId"]}, session_id=session_id)
                # Keep top-level authorization separate from normal resource loading.
                return
            # Ignore internal browser error and data pages.
            if destination.startswith(("chrome-error://", "chrome://", "about:", "data:")):
                # Allow internal browser pages to load without external authorization.
                await client.send.Fetch.continueRequest({"requestId": event["requestId"]}, session_id=session_id)
                # Skip external network guard checks for internal browser schemas.
                return
            # Prevent new-host navigation rather than inspecting content after it loads.
            if not self.is_allowed_url(destination):
                # Active or grounded-click pages may extend read-only navigation autonomously.
                if self._should_request_hostname(session_id):
                    # Preserve only this concrete HTTP(S) destination hostname.
                    parsed = urlparse(destination)
                    # Unsafe schemes and missing hosts remain blocked.
                    if parsed.scheme in {"http", "https"} and parsed.hostname:
                        # Add the deliberate host to this run's browser policy.
                        self.authorized_domains.add(parsed.hostname.lower())
                        # Continue the intended document request without a user interruption.
                        await client.send.Fetch.continueRequest({"requestId": event["requestId"]}, session_id=session_id)
                        # Do not execute the incidental-target denial path.
                        return
                # Fail only an unsolicited or unsafe intercepted request.
                await client.send.Fetch.failRequest({"requestId": event["requestId"], "errorReason": "BlockedByClient"}, session_id=session_id)
                # Do not continue a request after denying it.
                return
            # Let authorized navigation proceed with its original browser cookies.
            await client.send.Fetch.continueRequest({"requestId": event["requestId"]}, session_id=session_id)
        # Release the CDP reader immediately so continuation-command responses can arrive.
        def paused(event, session_id):
            """Schedule interception work without deadlocking the CDP event reader."""
            # The async CDP reader must not await a command whose response it needs to read.
            asyncio.create_task(handle_paused(event, session_id))
        # Register one actual CDP event handler in the selected Browser Use runtime.
        client.register.Fetch.requestPaused(paused)
        # Intercept document requests, including each redirected request.
        await client.send.Fetch.enable({"patterns": [{"resourceType": "Document", "requestStage": "Request"}]}, session_id=session)
        # Pause new page targets before their first external request can escape interception.
        if not self._popup_guard_installed:
            # Preserve Browser Use's own target bookkeeping callback.
            previous = client.register._registry._handlers.get("Target.attachedToTarget")

            # Install Fetch before resuming a newly created browser page.
            async def prepare_page(event, parent_session):
                """Guard a new page before release, then preserve the pinned runtime's bookkeeping."""
                # Ignore non-page targets such as service workers or background processes.
                if event.get("targetInfo", {}).get("type") != "page":
                    # Non-page targets do not need document interception.
                    return
                # Only page targets are paused by the requested filter.
                child = event["sessionId"]
                # Register intent and cleanup identity before the first child request can run.
                self._register_attached_page(child, event.get("targetInfo", {}).get("targetId", ""))
                # Configure interception before any requested popup URL can run.
                try:
                    # Enable Fetch interception on the child page session.
                    await client.send.Fetch.enable({"patterns": [{"resourceType": "Document", "requestStage": "Request"}]}, session_id=child)
                except Exception:
                    # Ignore session closed race conditions.
                    pass
                # Retain the installed Browser Use handler instead of silently replacing it.
                if previous is not None:
                    # Its return may be synchronous or awaitable in the pinned runtime.
                    result = previous(event, parent_session)
                    # Await bookkeeping only on this background task, never on the CDP reader.
                    if hasattr(result, "__await__"):
                        # Preserve target/session discovery before the page becomes usable.
                        await result
                # Release the page only after exact-host interception is installed.
                try:
                    # Let page execution proceed once guards are ready.
                    await client.send.Runtime.runIfWaitingForDebugger(session_id=child)
                except Exception:
                    # Ignore session closed race conditions.
                    pass

            # Never block the protocol reader while sending child-session commands.
            def attached(event, parent_session):
                """Schedule guarded page initialization without deadlocking CDP responses."""
                # Browser bookkeeping and Fetch setup require an independently running task.
                asyncio.create_task(prepare_page(event, parent_session))
            # Chain the existing handler through our guarded initialization wrapper.
            client.register.Target.attachedToTarget(attached)
            # Require interception only for page targets, retaining normal nonpage behavior.
            await client.send.Target.setAutoAttach({"autoAttach": True, "waitForDebuggerOnStart": True, "flatten": True, "filter": [{"type": "page", "exclude": False}, {"exclude": True}]})
            # Subsequent active-tab switches reuse the same root handler.
            self._popup_guard_installed = True

    # Initialize one persistent Browser Use session and its active page.
    def initialize(self, site, headful, session_reference=None):
        """Open an empty local browser, install policy, then navigate to the selected site."""
        # Resume ordinary cancellation behavior after a prior visibility-transfer cleanup.
        self._closing = False
        # Preserve controller-supplied authorized hosts.
        self.set_site(site, headful)
        # Respect explicit fake controller injection for isolated tests.
        if self.controller is not None:
            # Delegate only the transport contract, not production model decisions.
            self.controller.initialize(site=site, headful=headful, session_reference=session_reference)
            # No live loop or browser is needed in this injected mode.
            return
        # Import the selected installed library lazily.
        try:
            # Use the actual supported Browser constructor.
            from browser_use import Browser
        # Missing Browser Use is a setup failure, never a request to switch methods.
        except ImportError as exc:
            # Keep setup guidance explicit.
            raise RuntimeError("Browser Use is not installed") from exc
        # Create one event loop for this browser's entire lifecycle.
        self._loop = asyncio.new_event_loop()
        # Scope desktop launch options to this adapter's event loop, never global CreateProcess.
        options = browser_launch_options(headful)
        # Only a Windows headed launch needs an explicit subprocess desktop override.
        if options:
            # Retain the real bound implementation of this owned event loop.
            original_subprocess_exec = self._loop.subprocess_exec

            # Apply startup desktop settings only to subprocesses owned by this browser loop.
            async def launch_visible(protocol_factory, *arguments, **kwargs):
                """Launch this Browser Use instance's helpers on the user's visible desktop."""
                # Caller-supplied explicit options retain their supported precedence.
                for key, value in options.items():
                    # This does not affect another loop, process, thread, or executor.
                    kwargs.setdefault(key, value)
                # Delegate actual process creation to the installed Python event loop.
                return await original_subprocess_exec(protocol_factory, *browser_command(list(arguments), True), **kwargs)
            # Override only the loop instance that this adapter owns and later closes.
            self._loop.subprocess_exec = launch_visible
        # Run Browser Use coroutines on their owning background thread.
        self._thread = Thread(target=self._loop.run_forever, daemon=True, name="iba-browser-use")
        # Start the loop before submitting browser startup.
        self._thread.start()
        # A visibility transfer starts a new runtime with new CDP session identities.
        self._guarded_sessions = {}
        # Rebuild selected-page ownership from the new Browser Use CDP session.
        self._primary_sessions = set()
        # Discard click attribution belonging to the previous browser runtime.
        self._intent_sessions = set()
        # Discard target identities belonging to the previous browser runtime.
        self._guarded_targets = {}
        # Prevent a previous click interval from authorizing a new runtime target.
        self._navigation_intent_deadline = 0.0
        # The previous browser's root interception handler cannot be reused.
        self._popup_guard_installed = False
        # Do not carry an obsolete denied navigation into the restored session.
        self._blocked_url = ""
        # Isolate eligible reusable profile data by site and method.
        profile = ensure_session_dir(site, "browser_use").resolve()
        # Disable extensions and background warm-up that are not needed for local browsing.
        self._browser = Browser(executable_path=installed_chrome(), headless=not headful, user_data_dir=str(profile), enable_default_extensions=False, keep_alive=False, viewport={"width": 1280, "height": 800})
        # Start the selected Browser Use runtime.
        self._await(self._browser.start())
        # Open an empty page so authorization precedes the first real site request.
        self._page = self._await(self._browser.new_page("about:blank"))
        # Bring the browser window onto the visible desktop immediately so user sees it right away.
        if headful:
            # Force window restore and focus via Win32 APIs.
            require_visible_browser(profile, self.stop_event)
            # Update user interface monitor if available.
            if self.monitor is not None:
                # Notify UI that visible window is active.
                self.monitor.update_status("Visible browser window verified on the interactive desktop")
        # Install browser-level interception before navigation.
        self._await(self._install_guard())
        # Register the visible arrow before the selected destination replaces about:blank.
        self.install_visible_cursor()
        # Navigate using Browser Use's native page API.
        # Restore explicitly transferred authentication before any destination script executes.
        self.restore_transfer()
        # Navigate only after policy and eligible session state are installed.
        self._native("navigate", site)

    # Evaluate trusted application functions and normalize scalar-string results.
    def _evaluate(self, source):
        """Return actual evaluated data; normalize Browser Use's string-based API."""
        # Trim leading and trailing whitespace from JavaScript source.
        clean = source.strip()
        # Wrap comment-prefixed and async functions in the actor API's required arrow-function form.
        if clean.startswith("async ") or "await " in clean:
            # Wrap asynchronous function expressions in an awaited arrow wrapper.
            wrapped = "(async () => await (" + source + ")())"
        else:
            # Wrap synchronous function expressions in a standard arrow wrapper.
            wrapped = "() => (" + source + ")()"
        # Decode string JSON and False rather than relying on Python string truthiness.
        return decode_result(self._await(self._page.evaluate(wrapped)))

    # Save base64 screenshots using the actual installed return contract.
    def _screenshot(self, path):
        """Decode a Browser Use viewport PNG and save it to the unique artifact path."""
        # Request actual browser image data, not a synthetic page image.
        data = self._await(self._page.screenshot(format="png"))
        # Accept both supported byte and base64 transport forms.
        binary = data if isinstance(data, bytes) else base64.b64decode(data, validate=True)
        # Persist immutable evidence instead of overwriting a latest image.
        path.write_bytes(binary)
        # Let the shared observer check file existence.
        return str(path)

    # Implement native operations with Browser Use's Page and Element APIs.
    def _native(self, kind, target="", value=""):
        """Dispatch Browser Use input without positional DOM indices or JavaScript click()."""
        # Read an intercepted destination for the worker's authorization prompt.
        if kind == "blocked":
            # Copy the exact destination before clearing the pending request.
            url = self._blocked_url
            # Keep subsequent authorization events independent.
            self._blocked_url = ""
            # Return the common blocked-navigation contract.
            return {"url": url}
        # Use the installed Browser Use export API without writing sensitive state to disk.
        if kind == "session_export":
            # Return cookie state directly to the in-memory visibility-transfer helper.
            return self._await(self._browser.export_storage_state())
        # Restore explicit assistance state through the selected runtime's native CDP client.
        if kind == "session_restore":
            # Decode only application-owned transfer data, never model-generated scripts.
            state = json.loads(value)
            # The installed cookie setter accepts Chromium's native cookie schema.
            self._await(self._browser._cdp_set_cookies(state.get("cookies", [])))
            # Restore matching-origin storage before any destination JavaScript runs.
            script = """(state => { for (const entry of [...(state.origins||[]), ...(state.current?[state.current]:[])]) if(entry.origin===location.origin){for(const item of entry.localStorage||[])localStorage.setItem(item.name,item.value);for(const [name,value] of entry.sessionStorage||[])sessionStorage.setItem(name,value);} })(%s);""" % json.dumps(state)
            # Register the origin-scoped initializer in this owned page session.
            self._await(self._browser.cdp_client.send.Page.addScriptToEvaluateOnNewDocument({"source": script}, session_id=self._session_id))
            # The next real observation verifies the actual post-transfer interface.
            return {"success": True}
        # Register the passive pointer for the current and every future document.
        if kind == "install_cursor":
            # Convert the version-controlled function expression into a self-executing script.
            source = "(" + value + ")()"
            # Install before future document scripts so navigation cannot create a long cursor gap.
            self._await(self._browser.cdp_client.send.Page.addScriptToEvaluateOnNewDocument({"source": source}, session_id=self._session_id))
            # Apply the same implementation immediately to the current about:blank document.
            self._evaluate(value)
            # Read current CSS viewport geometry without another public adapter operation.
            viewport = self._evaluate("() => ({width:innerWidth,height:innerHeight})")
            # Move genuine browser input immediately so the current document displays the arrow.
            self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type":"mouseMoved","x":viewport["width"]/2,"y":viewport["height"]/2}, session_id=self._session_id))
            # Keep cursor lifecycle setup separate from task progress.
            return {"success": True}
        # A collection-only visible task must also show a genuine browser pointer.
        if kind == "pointer_start":
            # Read current CSS viewport dimensions through the selected actor.
            viewport = self._evaluate("() => ({width:innerWidth,height:innerHeight})")
            # Dispatch real browser input without moving the user's operating-system mouse.
            self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type": "mouseMoved", "x": viewport["width"] / 2, "y": viewport["height"] / 2}, session_id=self._session_id))
            # The passive marker observes this actual native input event.
            return {"success": True}
        # Native wheel input makes visible scrolling correspond to the actual red pointer.
        if kind == "wheel":
            # Coordinates and distance were resolved from the current requested scroll container.
            point = json.loads(value)
            # Move actual browser input, keeping the operating-system pointer free.
            self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type":"mouseMoved","x":point["x"],"y":point["y"]},session_id=self._session_id))
            # Dispatch actual wheel input to that same real container location.
            self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type":"mouseWheel","x":point["x"],"y":point["y"],"deltaX":0,"deltaY":point["delta"]},session_id=self._session_id))
            # Subsequent readiness/measurement checks verify actual movement.
            return {"success":True}
        # List current real actor pages.
        if kind == "tabs":
            # Preserve the selected method's own tab inventory.
            return self.manage_tabs()
        # Direct navigation must obey the common policy before issuing the command.
        if kind == "navigate":
            # Require exact-host permission before starting navigation.
            self.ensure_allowed_url(target)
            # A newly authorized retry must not inherit the previous denied URL.
            self._blocked_url = ""
            # Permit only redirects causally attached to this deliberate direct navigation.
            self._begin_navigation_intent(seconds=5.0)
            # Navigate the actual active actor page.
            self._await(self._page.goto(target))
            # Wait until the document is ready or an intercepted navigation requires help.
            deadline = time.monotonic() + 15
            # Browser Use goto returns before the document has necessarily loaded.
            while time.monotonic() < deadline:
                # A denied redirect must not degrade into an opaque navigation timeout.
                if self._blocked_url:
                    # Preserve the actual destination for authorization.
                    raise AuthorizationRequired(self._blocked_url)
                # Check readiness using the actual active page.
                try:
                    # A completed document can now produce a trustworthy observation.
                    ready = self._evaluate("() => document.readyState")
                    # Preserve the actual URL rather than trusting the requested URL.
                    current = self._await(self._page.get_url())
                    # Require an actual document rather than the initial empty tab.
                    if ready in {"interactive", "complete"} and current != "about:blank":
                        # Restore the genuine pointer as soon as the replacement document is usable.
                        if self.headful:
                            # Read the new page's real CSS viewport rather than using screenshot pixels.
                            viewport = self._evaluate("() => ({width:innerWidth,height:innerHeight})")
                            # Dispatch native input so the document-start arrow follows the actual browser point.
                            self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type":"mouseMoved","x":viewport["width"]/2,"y":viewport["height"]/2}, session_id=self._session_id))
                        # A fresh graph observation still verifies content and task progress.
                        return {"success": True, "url": current}
                # Transient context replacement is expected during navigation.
                except RuntimeError:
                    # Let the next readiness probe observe the new document.
                    pass
                # Keep readiness polling cancellable.
                self.stop_event.wait(0.05)
            # Do not claim a navigation completed solely because Page.navigate returned.
            raise TimeoutError("Browser Use document readiness timed out")
        # Restrict native interactions to implemented input operations.
        if kind not in {"click", "fill"}:
            # Never silently substitute direct DOM mutations.
            raise ValueError("Unsupported Browser Use native action")
        # Resolve the unique stable observed selector through Browser Use's actor API.
        selector = "[data-iba-id=" + json.dumps(target) + "]"
        # Find real actor elements, not a newly enumerated positional index.
        matches = self._await(self._page.get_elements_by_css_selector(selector))
        # The actor's ordinary CSS query does not pierce open shadow roots.
        if not matches:
            # Use the selected Browser Use session's own DOM backend, not another engine.
            flattened = self._await(self._browser.cdp_client.send.DOM.getFlattenedDocument({"depth": -1, "pierce": True}, session_id=self._session_id))
            # Match the exact application-generated attribute across accessible DOM roots.
            nodes = [node for node in flattened.get("nodes", []) if dict(zip(node.get("attributes", [])[::2], node.get("attributes", [])[1::2])).get("data-iba-id") == target]
            # Preserve ambiguity checks before constructing an actual actor element.
            if len(nodes) == 1:
                # Native input retains a concrete backend-node identity across shadow DOM.
                matches = [self._await(self._page.get_element(nodes[0]["backendNodeId"]))]
        # Stale and duplicate targets require another observation.
        if len(matches) != 1:
            # Do not choose a convenient first element.
            raise LookupError("Browser Use target is stale, ambiguous, or in an unsupported frame/shadow context")
        # Keep one real element identity for scrolling, hover, and input.
        element = matches[0]
        # Reveal this actual element before placing the pointer.
        self._await(element.evaluate("() => this.scrollIntoView({block:'center', behavior:'instant'})"))
        # Make the actual native trajectory visible without slowing headless execution.
        if self.headful:
            # Read geometry from the same concrete actor target used by the eventual click.
            box = self._await(element.get_bounding_box())
            # Use the previous actual browser mouse event as the trajectory's starting point.
            start = self._evaluate("() => window.__ibaPointer || {x:0,y:0}")
            # A missing real target geometry requires re-observation rather than guessed input.
            if box is None:
                # Refuse to animate or click a detached target.
                raise LookupError("Visible target has no current native geometry")
            # Bound visible movement to eight native steps, preserving exact final targeting.
            for step in range(1, 9):
                # Dispatch genuine browser input toward that target's actual CSS center.
                self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type":"mouseMoved","x":start["x"]+(box["x"]+box["width"]/2-start["x"])*step/8,"y":start["y"]+(box["y"]+box["height"]/2-start["y"])*step/8}, session_id=self._session_id))
                # Short visible interpolation remains promptly cancellable.
                self.stop_event.wait(0.016)
        # Optional overlay closure avoids a redundant hover that can race a replacement modal.
        dismissal = kind == "click" and value == "__iba_optional_overlay__"
        # Ordinary actions retain the actor library's explicit native hover behavior.
        if not dismissal:
            # Native hover moves actual browser input and the passive cursor together.
            self._await(element.hover())
        # Dispatch normal trusted click input through the installed library.
        if kind == "click":
            # Attribute only targets created immediately by this concrete agent input.
            self._begin_navigation_intent()
            # The library checks geometry/actionability before input.
            self._await(element.click())
        # Native fill uses the installed input implementation rather than setting .value.
        else:
            # Click the target input field through the actor to ensure visible focus.
            self._await(element.click())
            # Framework-controlled inputs receive the appropriate input behavior.
            self._await(element.fill(value))
        # A click may replace the document after its target received native input.
        if kind == "click" and self.headful:
            # Re-dispatch the last target point so the new document's init script becomes visible.
            self._await(self._browser.cdp_client.send.Input.dispatchMouseEvent({"type":"mouseMoved","x":box["x"]+box["width"]/2,"y":box["y"]+box["height"]/2}, session_id=self._session_id))
        # Report the exact identity that received input.
        return {"success": True, "target": target}

    # Preserve explicit controller injection for deterministic contract tests.
    def observe(self):
        """Use shared live observation or a supplied normalized test controller."""
        # Injected controllers own only their fake transport state.
        if self.controller is not None:
            # Import lazily to keep missing-library setup tests isolated.
            from domain.models import BrowserObservation
            # Read the controller's normalized state.
            result = self.controller.observe()
            # Accept a shared record or construct it from a mapping.
            return result if isinstance(result, BrowserObservation) else BrowserObservation(**result)
        # Production uses the exact same inspection and image contract as CLI/MCP.
        return super().observe()

    # Keep fake transport support while production uses the shared policy.
    def execute(self, decision):
        """Validate common production behavior or delegate an explicitly injected fake."""
        # Do not start a live browser for a contract-test controller.
        if self.controller is not None:
            # Enforce navigation policy even for an injected controller.
            if decision.kind == "navigate":
                # Ensure fake tests exercise the real shared authorization rule.
                self.ensure_allowed_url(decision.target)
            # Delegate the normalized operation to the explicit test controller.
            return self.controller.execute(decision)
        # Use common stale-target, policy, and effect checks in production.
        return super().execute(decision)

    # Return actual page identities rather than invented default tab zero.
    def manage_tabs(self):
        """Describe current Browser Use targets and the selected actor page."""
        # Preserve deterministic tab contracts for injected tests.
        if self.controller is not None:
            # A fake controller must provide its own tab inventory.
            return self.controller.manage_tabs()
        # Query the selected runtime's page actors.
        pages = self._await(self._browser.get_pages())
        # Use real target IDs so closing another tab cannot silently retarget an index.
        return [{"index": index, "id": page._target_id, "url": self._await(page.get_url()), "active": page._target_id == self._page._target_id} for index, page in enumerate(pages)]

    # Dispatch native keyboard input to the active Browser Use page.
    def _press(self, key):
        """Press a permitted browsing key through the installed actor API."""
        # Let Browser Use dispatch actual keyboard events.
        self._await(self._page.press(key))
        # A fresh observation establishes the resulting effect.
        return {"success": True, "action": "press"}

    # Validate and switch/close actual target identities.
    def _tab_action(self, kind, target):
        """Select a concrete page actor, refreshing its document interception guard."""
        # Obtain current actors instead of retaining a stale positional list.
        pages = self._await(self._browser.get_pages())
        # Resolve by real ID or explicit valid index.
        matches = [page for index, page in enumerate(pages) if page._target_id == target or str(index) == str(target)]
        # Missing tabs must not fall back to the first page.
        if len(matches) != 1:
            # Ask the graph to re-observe current browser contexts.
            raise LookupError("Unknown Browser Use tab")
        # Close only the requested target through the selected runtime.
        if kind == "close_tab":
            # Use the Browser Use-owned CDP client for page lifecycle.
            self._await(self._browser.cdp_client.send.Target.closeTarget({"targetId": matches[0]._target_id}))
            # Select a surviving page only when the active page was closed.
            if matches[0]._target_id == self._page._target_id:
                # Obtain actual survivors after close.
                remaining = self._await(self._browser.get_pages())
                # Refuse a missing active context explicitly.
                if not remaining:
                    # The agent cannot act without a page.
                    raise LookupError("No browser tab remains")
                # Keep the surviving concrete page actor.
                self._page = remaining[0]
        # Switch to the uniquely selected actual actor.
        else:
            # Preserve exact page identity across re-observation.
            self._page = matches[0]
        # Install the document guard for the new active actor.
        self._await(self._install_guard())
        # A newly selected or surviving tab needs its own document-start cursor registration.
        self.install_visible_cursor()
        # Re-observation verifies URL and active context.
        return {"success": True, "action": kind}

    # Stop asynchronous work and retain eligible reusable profile data.
    def close_or_detach(self):
        """Release the owned browser/loop even after Stop or a failed initialization."""
        # Fake controllers own their own cleanup.
        if self.controller is not None:
            # No event-loop thread was created in injected mode.
            self.controller.close_or_detach()
            # Avoid live cleanup on a nonexistent browser.
            return
        # Permit cleanup without clearing the supervisor's cancellation signal.
        self._closing = True
        # Always stop the event loop after browser shutdown attempts.
        try:
            # A setup failure may occur before the browser exists.
            if self._browser is not None:
                # A native desktop launcher is a wrapper PID; close the actual owned browser first.
                if self.headful:
                    # Prevent automatic reconnect while intentionally closing this owned session.
                    self._browser._intentional_stop = True
                    # Browser.close targets only this Browser Use instance's CDP connection.
                    try:
                        # Graceful native browser shutdown also flushes eligible profile state.
                        self._await(self._browser.cdp_client.send.Browser.close())
                    # The WebSocket may close before acknowledging the successful shutdown.
                    except Exception:
                        # The installed runtime cleanup below still reaps its wrapper/resources.
                        pass
                # Let the installed library release its process, CDP client, and runtime state.
                self._await(self._browser.kill())
        # Ensure a failed browser shutdown does not leak the owning event-loop thread.
        finally:
            # Stop only this adapter's loop.
            if self._loop and self._loop.is_running():
                # Schedule shutdown on the loop's owning thread.
                self._loop.call_soon_threadsafe(self._loop.stop)
            # Join only the adapter-owned thread.
            if self._thread:
                # Keep cleanup bounded.
                self._thread.join(timeout=2)
            # Remove runtime references after cleanup.
            self._browser = None
