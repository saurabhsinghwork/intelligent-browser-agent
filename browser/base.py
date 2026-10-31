"""Shared deterministic browser behavior independent of the chosen transport.

Concrete adapters own only evaluation, native input, screenshots, tabs, and session
lifecycle. This base owns exact-host authorization, stable observations, measured
scrolling, read-only action policy, and real-effect checks.
"""
# Serialize trusted script arguments without JavaScript string interpolation.
import json
# Fingerprint observed UI state without relying on a model's success assertion.
import hashlib
# Resolve source scripts and immutable artifacts independently of the launch directory.
from pathlib import Path
# Bound local readiness waits and generate unique observation/image identities.
import time
# Allocate unique IDs for observations, scripts, and immutable image artifacts.
from uuid import uuid4
# Parse exact hostname boundaries and relative links safely.
from urllib.parse import urlparse, urljoin
# Check cancellation without blocking on long animation sleeps.
from threading import Event
# Match specifically disallowed consequential controls in the initial release.
import re
# Return the shared typed records consumed by LangGraph.
from domain.models import BrowserObservation
# Route permission and human-only steps through explicit interruption paths.
from domain.errors import AuthorizationRequired, AssistanceRequired
# Group safe sibling subdomains while preserving exact planned external grants.
from services.identity import site_family

# Locate version-controlled scripts relative to this module.
SCRIPT_ROOT = Path(__file__).resolve().parent
# Keep artifacts local to the project regardless of Streamlit's working directory.
ARTIFACT_ROOT = SCRIPT_ROOT.parent / "data" / "run_artifacts"


# Normalize result wrappers from CLI, MCP, and Browser Use into ordinary JSON values.
def decode_result(value):
    """Unwrap tool-readable Result sections and JSON strings without truthiness coercion."""
    # Accept dictionaries that already contain the requested typed result.
    if isinstance(value, dict):
        # Prefer explicit structured values over readable command transcripts.
        if "data" in value:
            # Decode recursively in case the structured value itself is JSON text.
            return decode_result(value["data"])
        # Parse a readable-only transport wrapper but retain actual result dictionaries.
        if set(value).issubset({"text"}) and "text" in value:
            # Share the exact same readable-result parser across both Playwright methods.
            return decode_result(value["text"])
        # Preserve actual mappings such as page state and action results.
        return value
    # Native arrays, booleans, and null are already normalized.
    if not isinstance(value, str):
        # Avoid converting a real False into a truthy string.
        return value
    # Remove transport headings without trimming extracted JSON field contents.
    text = value.strip()
    # Official Playwright tools put evaluated results under a readable heading.
    if "### Result" in text:
        # Isolate the Result section before command transcripts and page snapshots.
        text = text.split("### Result", 1)[1].split("\n### ", 1)[0].strip()
    # Parse JSON-compatible scalar, array, or object output.
    try:
        # JSON decoding preserves source text inside string values.
        return json.loads(text)
    # Browser Use returns Python-style Boolean spellings as strings.
    except (json.JSONDecodeError, TypeError):
        # Interpret only exact scalar spellings, never arbitrary nonempty strings.
        if text in {"True", "False"}:
            # Return a real Boolean for bottom detection and native action outcomes.
            return text == "True"
        # Preserve an unstructured diagnostic for the caller to classify explicitly.
        return text


# Provide common observations, authorization, and measured interaction behavior.
class BaseBrowserAdapter:
    """Own one run's policy, artifacts, stable targets, and cancellation reference."""

    # Initialize state without launching any provider or browser process.
    def __init__(self):
        """Allocate an isolated artifact directory and empty run-scoped browser state."""
        # Wait for explicit selection before permitting normal website navigation.
        self.selected_domain = ""
        # Treat ordinary regional and www sibling hosts as one selected website family.
        self.selected_site_family = ""
        # Headless is the safe default until the user's visibility choice is applied.
        self.headful = False
        # Grants apply to exact additional hostnames, never implicit subdomains.
        self.authorized_domains = set()
        # Share cancellation with the supervisor when a run starts.
        self.stop_event = Event()
        # Support live artifact publication without depending on Streamlit.
        self.monitor = None
        # Keep this run's images separate from every other run.
        self.run_id = uuid4().hex
        # Avoid artifact collisions and repeatedly overwritten latest screenshots.
        self._screenshot_dir = ARTIFACT_ROOT / self.run_id
        # Bind actions to the most recent actual observation.
        self._last_observation = None
        # Distinguish a fresh final collection capture from the older pre-scroll observation.
        self._collection_observation = None
        # Record the original URL for session handoff.
        self.site = ""
        # Hold assistance-transfer cookies/storage only in this owned runtime, never checkpoints.
        self._transfer_state = None
        # Cache already captured future viewports from one CLI/MCP traversal batch.
        self._capture_queue = []
        # Bind cached viewports to one exact extraction scope and scroll container.
        self._capture_queue_key = None
        # Four viewports amortize transport startup while keeping progress and Stop responsive.
        self._capture_batch_size = 4

    # Capture eligible authentication state before a headless/headful lifecycle transition.
    def prepare_transfer(self):
        """Retain session cookies and current-origin storage in memory for the next browser."""
        # Persistent profile shutdown alone does not reliably flush every installed executor.
        self._transfer_state = self._native("session_export")
        # Capture current-origin storage without persisting its contents to logs or checkpoints.
        storage = self._evaluate("() => ({origin:location.origin,localStorage:Object.entries(localStorage).map(([name,value])=>({name,value})),sessionStorage:Object.entries(sessionStorage)})")
        # Preserve current-origin local/session storage alongside cookie state.
        self._transfer_state["current"] = storage

    # Restore in-memory assistance state before the first website navigation.
    def restore_transfer(self):
        """Install cookies and origin-scoped storage only when a transfer was requested."""
        # Ordinary startup reuses its isolated profile without reading another session.
        if self._transfer_state is not None:
            # Native context APIs install state before the destination scripts execute.
            self._native("session_restore", value=json.dumps(self._transfer_state))
            # Release sensitive transfer memory after applying it to the owned browser.
            self._transfer_state = None

    # Configure policy while preserving grants across adapter initialization.
    def set_site(self, site, headful, authorized_domains=None):
        """Set the exact selected host and visibility; replace grants only when provided."""
        # Accept a bare host only at configuration boundaries.
        normalized = site if "://" in site else "https://" + site
        # Persist the starting destination for browser/session initialization.
        self.site = normalized
        # Normalize case but preserve the exact hostname boundary.
        self.selected_domain = (urlparse(normalized).hostname or "").lower()
        # Remember the registrable site boundary independently from a particular subdomain.
        self.selected_site_family = site_family(self.selected_domain)
        # Retain the requested visibility mode for screenshot and cursor behavior.
        self.headful = bool(headful)
        # Initialization must not erase grants already supplied by the controller.
        if authorized_domains is not None:
            # Each explicit grant applies to precisely one hostname.
            self.authorized_domains = {host.lower() for host in authorized_domains}

    # Evaluate exact-host authorization for a top-level browsing destination.
    def is_allowed_url(self, url):
        """Allow HTTP(S) on selected/granted hosts, relative URLs, and initial about:blank."""
        # Keep the initial empty tab and internal browser error pages valid without allowing arbitrary executable schemes.
        if url == "about:blank" or url.startswith(("chrome-error://", "about:", "chrome://")):
            # No external website has been visited in this state.
            return True
        # Resolve relative links against the selected destination.
        parsed = urlparse(urljoin(self.site or "https://invalid.local", url))
        # Deny javascript, data, file, and other non-web destinations.
        if parsed.scheme not in {"http", "https"}:
            # A missing hostname must never bypass scheme validation.
            return False
        # Compare exact normalized hosts; child hosts require their own grant.
        # Normalize the proposed host once for exact and family comparison.
        host = (parsed.hostname or "").lower()
        # Permit the selected website's regional/www sibling hosts and explicit planned grants.
        return host in {self.selected_domain, *self.authorized_domains} or bool(self.selected_site_family and site_family(host) == self.selected_site_family)

    # Grant a deliberate information-gathering destination without interrupting the user.
    def authorize_planned_url(self, url):
        """Authorize one explicit HTTP(S) action target while rejecting unsafe schemes."""
        # Resolve relative destinations against the selected site.
        parsed = urlparse(urljoin(self.site or "https://invalid.local", url))
        # Never auto-authorize executable, local-file, or malformed destinations.
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            # Preserve the existing typed authorization failure for unsafe targets.
            raise AuthorizationRequired(url)
        # Add only this deliberate concrete hostname for the current run.
        self.authorized_domains.add(parsed.hostname.lower())
        # Return the original destination for convenient adapter dispatch.
        return url

    # Fail with actionable destination data before navigating to another host.
    def ensure_allowed_url(self, url, external_authorized=False):
        """Raise AuthorizationRequired unless this exact destination host was authorized."""
        # Preserve the legacy explicit one-operation authorization contract.
        if external_authorized:
            # Callers still need to publish a persistent grant when installing browser guards.
            return
        # Require concrete permission before any unauthorized browsing action.
        if not self.is_allowed_url(url):
            # Keep the destination available for a human authorization prompt.
            raise AuthorizationRequired(url)

    # Check cancellation inside local collection and readiness loops.
    def check_cancelled(self):
        """Raise InterruptedError as soon as the supervisor signals Stop."""
        # User Pause freezes even local collection steps between graph cycles.
        if self.monitor is not None and hasattr(self.monitor, "gate"):
            # The worker monitor keeps this wait cancellable.
            self.monitor.gate()
        # No browser action may start after a stop request is observed.
        if self.stop_event.is_set():
            # Let the controller preserve partial evidence and clean up owned resources.
            raise InterruptedError("Stopped by user")

    # Execute one trusted page-inspection function through the selected transport.
    def probe(self, mode="observe", **arguments):
        """Return typed page measurements or exact blocks; raise on malformed transport data."""
        # Honour Stop before making another browser call.
        self.check_cancelled()
        # Direct movement invalidates any future viewports captured before that movement.
        if mode in {"reset", "scroll"}:
            # Discard only unconsumed traversal cache, never committed evidence.
            self.invalidate_capture_batch()
        # Load application-owned code; no model-provided script is ever evaluated.
        source = (SCRIPT_ROOT / "page_probe.js").read_text(encoding="utf-8")
        # Encode arguments as JSON to preserve quotes and control characters safely.
        payload = json.dumps({"mode": mode, **arguments}, ensure_ascii=False)
        # Wrap the reusable function so adapters only need a zero-argument evaluation API.
        result = decode_result(self._evaluate("() => (" + source + ")(" + payload + ")"))
        # Inspection must produce an object, not a readable error transcript.
        if not isinstance(result, dict):
            # Refuse to treat malformed evaluation text as a valid observation.
            raise RuntimeError("Browser inspection did not return a structured object")
        # Return normalized measurements without truthiness guessing.
        return result

    # Discard speculative viewport cache after navigation, input, reset, or explicit limits.
    def invalidate_capture_batch(self):
        """Clear only unconsumed browser-side traversal results."""
        # Future captures no longer describe the browser after a state-changing action.
        self._capture_queue = []
        # Remove its scope binding at the same time.
        self._capture_queue_key = None

    # Build the native input wrapper shared by CLI and MCP transports.
    def _native(self, kind, target="", value=""):
        """Run application-owned native Playwright input through the selected adapter."""
        # Refresh exact-host grants before every native operation.
        arguments = {"kind": kind, "target": target, "value": value, "hosts": [self.selected_domain, *sorted(self.authorized_domains)], "site_family": self.selected_site_family, "headful": self.headful}
        # Read trusted backend code rather than accepting model-generated JavaScript.
        source = (SCRIPT_ROOT / "native_playwright.js").read_text(encoding="utf-8")
        # Preserve arbitrary search strings as encoded data, not interpolated code.
        try:
            # Execute only the application-owned operation in the selected method.
            return decode_result(self._run_code("async (page) => (" + source + ")(page, " + json.dumps(arguments) + ")"))
        # Navigation guards may surface a generic tool error after blocking a redirect.
        except Exception as exc:
            # Reading the pending destination must not recursively re-read itself.
            if kind != "blocked":
                # Distinguish a concrete authorization gate from an ordinary transport error.
                blocked = self._native("blocked")
                # Preserve the actual denied destination for the UI and authorized retry.
                if isinstance(blocked, dict) and blocked.get("url"):
                    # The caller must explicitly authorize this exact hostname.
                    raise AuthorizationRequired(blocked["url"]) from exc
            # Keep unrelated native-input errors available for bounded recovery.
            raise

    # Register the visible cursor before opening the selected website.
    def install_visible_cursor(self):
        """Install the passive arrow in the current and every future main document."""
        # Headless runs must not add a visual overlay or unnecessary native input.
        if not self.headful:
            # Preserve the unchanged background execution path.
            return
        # Read only the version-controlled cursor implementation.
        source = (SCRIPT_ROOT / "cursor_init.js").read_text(encoding="utf-8")
        # Let the selected executor register the script at document start.
        self._native("install_cursor", value=source)

    # Use native wheel input for visible runs while retaining efficient headless measurements.
    def advance_scroll(self, scope, container, direction="down"):
        """Place the actual pointer inside the requested panel before a real visible scroll."""
        # Headless collection needs no visible pointer or wheel animation.
        if not self.headful:
            # Preserve the established deterministic instant-scroll path.
            return self.probe("scroll", target=container, direction=direction)
        # Resolve native input geometry from the current actual requested content/container.
        point = self.probe("scroll_target", scope=scope, target=container, direction=direction)
        # Measure the intended container before dispatch because overlays can intercept native wheel input.
        before = self.probe("measure", target=container)
        # The same concrete pointer position receives the native wheel event.
        self._native("wheel", value=json.dumps(point))
        # Wait for real rendering before checking whether this container moved.
        capture, metrics = self.settle(scope, container)
        # Native wheel latching/overlays may consume input without moving the requested container.
        if metrics["top"] == before["top"] and not metrics["bottom"]:
            # Move only the already-resolved container; never guess another panel or claim a false bottom.
            self.probe("scroll", target=container, direction=direction)
            # Confirm actual rendered movement and source before continuing.
            capture, metrics = self.settle(scope, container)
        # Preserve typed measurements rather than treating the input event as proof.
        return metrics

    # Combine scroll, readiness, capture, and screenshot in one CLI/MCP round trip.
    def capture_view(self, scope, container, advance=False):
        """Return a stable viewport with immutable image evidence through the selected executor."""
        # Preserve pause/stop before another browser-side batch begins.
        self.check_cancelled()
        # Bind prefetched viewports to one exact source scope and real container.
        key = (scope, container)
        # A sequential collector may consume a viewport already captured after genuine movement.
        if advance and self._capture_queue and self._capture_queue_key == key:
            # Return the next source/screenshot pair without another process or RPC startup.
            return self._capture_queue.pop(0)
        # A new scope, reset, or nonsequential request invalidates unused future captures.
        if self._capture_queue:
            # Preserve only committed evidence; queued views have not yet been accepted by the collector.
            self.invalidate_capture_batch()
        # Allocate immutable evidence before submitting the selected transport operation.
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        # Keep every viewport image distinct within this owned run.
        path = self._screenshot_dir / ("collect_" + uuid4().hex + ".png")
        # CLI and MCP can execute a whole trusted Playwright function in one operation.
        if hasattr(self, "_run_code"):
            # Reuse the exact shared inspection and readiness logic.
            inspect = (SCRIPT_ROOT / "page_probe.js").read_text(encoding="utf-8")
            # The browser-side loop avoids command startup for every readiness probe.
            settle = (SCRIPT_ROOT / "settle_probe.js").read_text(encoding="utf-8")
            # Load the application-owned multi-viewport executor rather than generating model code.
            batch = (SCRIPT_ROOT / "capture_batch.js").read_text(encoding="utf-8")
            # Preallocate immutable screenshot paths for this bounded transport batch.
            paths = [str(path)] + [str(self._screenshot_dir / ("collect_" + uuid4().hex + ".png")) for _ in range(self._capture_batch_size - 1)]
            # Encode only concrete collection arguments and application-owned source strings.
            payload = {"scope": scope, "container": container, "advance": advance, "headful": self.headful, "paths": paths, "batchSize": self._capture_batch_size}
            # Execute several measured viewports through one CLI process or MCP request.
            source = "async page => (" + batch + ")(page," + json.dumps(payload) + "," + json.dumps(inspect) + "," + json.dumps(settle) + ")"
            # Run the bounded batch through the actual chosen CLI or MCP transport.
            result = decode_result(self._run_code(source))
            # Refuse malformed batch results instead of claiming source coverage.
            if not isinstance(result, dict) or not isinstance(result.get("views"), list) or not result["views"]:
                # Preserve the actual adapter incompatibility for bounded recovery.
                raise RuntimeError("Viewport batch returned no source captures")
            # Normalize every captured source/screenshot pair before exposing it to the collector.
            views = [(item["capture"], item["metrics"]) for item in result["views"]]
            # Cache later viewports only for this same sequential container traversal.
            self._capture_queue = views[1:]
            # Bind queued movement evidence to its actual extraction context.
            self._capture_queue_key = key if self._capture_queue else None
            # Return the first viewport in source order; later calls consume the cache.
            return views[0]
        # Browser Use uses its own actor APIs without routing through Playwright.
        before = None
        # Keep visible movement and its first stable capture in this one collection step.
        if advance:
            # Preserve the exact starting position for intercepted-wheel recovery.
            before = self.probe("measure", target=container)
            # Headful Browser Use must place genuine input in the requested content panel.
            if self.headful:
                # Resolve native CSS coordinates from current page geometry.
                point = self.probe("scroll_target", scope=scope, target=container, direction="down")
                # Dispatch one real wheel operation through the selected Browser Use runtime.
                self._native("wheel", value=json.dumps(point))
            # Headless Browser Use retains deterministic instant measured movement.
            else:
                # Advance only the exact selected container.
                self.probe("scroll", target=container, direction="down")
        # Await one shared local readiness function through the actual actor.
        capture, metrics = self.settle(scope, container)
        # A fixed overlay may consume native wheel input without moving the requested panel.
        if advance and self.headful and metrics["top"] == before["top"] and not metrics["bottom"]:
            # Recover only the already-resolved container rather than guessing another scroll target.
            self.probe("scroll", target=container, direction="down")
            # Recapture once after measured fallback movement, without a duplicate normal settle.
            capture, metrics = self.settle(scope, container)
        # Capture the real selected-method image.
        self._screenshot(path)
        # Supply the immutable image path to the same collector.
        capture["screenshot_path"] = str(path)
        # All three methods preserve the same measured-source contract.
        return capture, metrics

    # Batch mechanical readiness work inside one selected-backend operation.
    def settle(self, scope, container, bottom=False):
        """Return stable source/measurements without repeated CLI/RPC calls per quiet interval."""
        # Preserve cancellation before submitting another bounded browser observation.
        self.check_cancelled()
        # Load only version-controlled application code, never provider-generated scripts.
        inspect = (SCRIPT_ROOT / "page_probe.js").read_text(encoding="utf-8")
        # Use identical readiness logic for all three actual transports.
        settle = (SCRIPT_ROOT / "settle_probe.js").read_text(encoding="utf-8")
        # Preserve scope/identity as encoded data.
        request = json.dumps({"scope": scope, "container": container, "bottom": bottom})
        # The actor API awaits the returned Promise; CLI/MCP execute it in their selected runtime.
        result = decode_result(self._evaluate("() => (" + settle + ")((" + inspect + "), " + request + ")"))
        # Require concrete typed captures instead of a readable success transcript.
        if not isinstance(result, dict) or "capture" not in result:
            # Surface incompatible transport results as actual failures.
            raise RuntimeError("Readiness inspection returned no structured capture")
        # Return matching source and geometry from one stable operation.
        return result["capture"], result["metrics"]

    # Promote the final deterministic collection capture into a reusable graph observation.
    def remember_collection_capture(self, data):
        """Bind final source, targets, geometry, and screenshot without rereading the page."""
        # A collection capture must include the same immutable image evidence as an observation.
        image_path = data.get("screenshot_path", "")
        # Missing images cannot become multimodal verification evidence.
        if not image_path or not Path(image_path).is_file():
            # Keep the previous observation and let normal verification observe again.
            return None
        # Allocate an identity that binds any following action to this exact capture.
        observation_id = uuid4().hex
        # Ignore cursor animation while retaining meaningful current UI properties.
        fingerprint = hashlib.sha256(json.dumps([data["url"], data["text"], data["elements"]], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        # Scrolling does not change tab ownership, so preserve the last verified inventory.
        tabs = list(self._last_observation.tabs) if self._last_observation is not None else []
        # Construct the same provider-neutral record returned by ordinary observation.
        observation = BrowserObservation(url=data["url"], title=data.get("title", ""), text=data.get("text", ""), elements=data["elements"], screenshot_path=image_path, tabs=tabs, all_screenshots=[image_path], observation_id=observation_id, geometry={"viewport": data["viewport"], "containers": data["containers"], "regions": data.get("regions", []), "limitations": data["limitations"]}, links=data["links"], fingerprint=fingerprint)
        # Bind future targeting and verification to the actual final collected state.
        self._last_observation = observation
        # Mark this record as specifically matching the completed collection position.
        self._collection_observation = observation
        # Return the reusable record to orchestration without another transport call.
        return observation

    # Capture a stable screenshot alongside current structured information.
    def observe(self):
        """Return full source text plus observation-bound targets and immutable image evidence."""
        # Surface a blocked redirect or popup before reasoning on a stale parent page.
        blocked = self._native("blocked")
        # Only explicit user authorization can resume the proposed new hostname.
        if isinstance(blocked, dict) and blocked.get("url"):
            # Do not treat an unchanged parent screen as a successful popup action.
            raise AuthorizationRequired(blocked["url"])
        # Read structured state once; verification can reuse this fresh observation.
        data = self.probe()
        # Enforce policy before sending newly observed content to any reasoning model.
        self.ensure_allowed_url(data["url"])
        # Install a passive event-driven marker only for visible execution.
        if self.headful:
            # Injection is idempotent and never independently resolves or scrolls a target.
            installed = self._evaluate((SCRIPT_ROOT / "cursor_init.js").read_text(encoding="utf-8"))
            # A collection-only task still needs a visible pointer before any click occurs.
            if installed:
                # Move native browser input once; the overlay follows the actual mouse event.
                self._native("pointer_start")
        # Allocate a unique image filename for this observation.
        observation_id = uuid4().hex
        # Create only the run-owned artifact directory.
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        # Capture the actual viewport with a stable absolute path.
        image_path = self._screenshot(self._screenshot_dir / (observation_id + ".png"))
        # Require images for the live multimodal workflow instead of silently losing vision.
        if not image_path or not Path(image_path).is_file():
            # Surface screenshot failures as concrete browser errors.
            raise RuntimeError("Browser screenshot was not saved")
        # Fingerprint meaningful UI properties rather than cursor overlay animation.
        fingerprint = hashlib.sha256(json.dumps([data["url"], data["text"], data["elements"]], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        # Preserve source text while exposing actual geometry and all discovered links.
        observation = BrowserObservation(url=data["url"], title=data.get("title", ""), text=data.get("text", ""), elements=data["elements"], screenshot_path=str(image_path), tabs=self.manage_tabs(), all_screenshots=[str(image_path)], observation_id=observation_id, geometry={"viewport": data["viewport"], "containers": data["containers"], "regions": data.get("regions", []), "limitations": data["limitations"]}, links=data["links"], fingerprint=fingerprint)
        # Bind the next interactive action to this actual observation.
        self._last_observation = observation
        # Publish immutable images during execution instead of waiting for graph completion.
        if self.monitor is not None:
            # Keep UI publication independent of browser transport details.
            self.monitor.add_screenshot(str(image_path))
        # Return one reusable observation to the graph.
        return observation

    # Execute only agreed read-only browsing operations.
    def execute(self, decision):
        """Run a validated action and return measured before/after evidence or a typed blocker."""
        # Stop before dispatching another operation.
        self.check_cancelled()
        # Any model-directed input invalidates browser-side future viewport captures.
        self.invalidate_capture_batch()
        # Direct navigation requires a concrete exact-host grant.
        if decision.kind == "navigate":
            # A grounded agent plan may autonomously grant its deliberate read-only destination.
            self.authorize_planned_url(decision.target)
            # Let browser-level guards also inspect redirects.
            return self._native("navigate", decision.target)
        # Scroll an explicit measured container in the requested direction.
        if decision.kind == "scroll":
            # Capture the actual starting position for effect verification.
            before = self.probe("measure", target=decision.target or "window")
            # Use the same typed scroll implementation for every transport.
            after = self.advance_scroll("body", decision.target or "window", decision.value or "down")
            # At an actual end, report no movement instead of pretending a scroll progressed.
            return {"success": after["top"] != before["top"], "before": before, "after": after, "action": "scroll"}
        # Wait briefly with cancellation rather than a long unconditional sleep.
        if decision.kind == "wait":
            # The browser/model observation on the next cycle establishes readiness.
            self.stop_event.wait(0.25)
            # No content claim is implied by waiting.
            return {"success": True, "action": "wait"}
        # Tab actions require concrete adapter identities.
        if decision.kind in {"switch_tab", "close_tab"}:
            # The selected backend validates indices instead of defaulting to tab zero.
            return self._tab_action(decision.kind, decision.target)
        # Keyboard input is dispatched natively, not as synthetic DOM events.
        if decision.kind == "press":
            # Keep the permitted keyboard language narrow for the initial read-only release.
            if decision.target not in {"Enter", "Escape", "Tab", "PageDown", "PageUp", "ArrowDown", "ArrowUp"}:
                # Do not permit arbitrary shortcuts that could trigger unrelated browser behavior.
                raise ValueError("Unsupported browsing key")
            # Use the selected adapter's actual keyboard interface.
            return self._press(decision.target)
        # Reject unsupported or terminal decisions at the browser boundary.
        if decision.kind not in {"click", "fill"}:
            # Collection and finalization belong to the shared services/graph.
            raise ValueError("This decision is not a browser action.")
        # Require the current observation for live model-driven input.
        if self._last_observation and decision.observation_id != self._last_observation.observation_id:
            # A stale or omitted ID requires another grounded decision.
            raise LookupError("Action observation is stale or missing")
        # A model may target only an element actually included in its current observation.
        if self._last_observation and decision.target not in {item.get("id_label") for item in self._last_observation.elements}:
            # Give the next reasoning cycle concrete observed alternatives for its explicitly proposed link URL.
            matches = [{"id":item["id_label"],"text":item.get("text", ""),"url":item.get("href")} for item in self._last_observation.elements if item.get("href") and item.get("href") in decision.links]
            # Reject fabricated identities without executing a guessed replacement click.
            raise LookupError("Target was not present in the current observation. Observed targets for proposed URLs: " + json.dumps(matches[:8], ensure_ascii=False))
        # Resolve the exact real node to inspect current properties before input.
        target = self.probe("resolve", target=decision.target)
        # Disabled controls cannot be treated as successfully clicked.
        if target["disabled"]:
            # Force recovery to choose another actual UI path.
            raise LookupError("Target is disabled")
        # Navigation from a link obeys the same policy as direct goto.
        if target["href"]:
            # Grounded observed links may autonomously extend read-only research navigation.
            self.authorize_planned_url(target["href"])
        # Human credentials are entered during explicit assistance, not by the agent.
        if target["type"] == "password" or re.search(r"\b(sign in|log in|login)\b", target["text"], re.I) and not re.search(r"\b(close|dismiss|not now|no thanks|maybe later|skip)\b", target["text"], re.I):
            # Preserve the current page for manual login and later re-observation.
            raise AssistanceRequired("login")
        # Exclude consequential actions from the initial release regardless of model reasoning.
        if re.search(r"\b(buy|purchase|checkout|delete|send|subscribe|sign up|register|join now|apply|set alert|accept all)\b", target["text"], re.I):
            # Never silently expand the approved scope or optional-cookie policy.
            raise PermissionError("This control is outside the information-gathering release")
        # Native input uses the same resolved identity as the passive cursor.
        result = self._native(decision.kind, decision.target, decision.value)
        # A fill succeeds only when the real input retains the requested value.
        if decision.kind == "fill":
            # Check the actual field, not only a successful transport return.
            actual = self.probe("resolve", target=decision.target)
            # Keep framework-controlled field failures visible to recovery.
            result["success"] = actual["value"] == decision.value
        # Return backend evidence for the graph's fresh post-action observation.
        return result

    # Retain a compatibility entry point without the previous six-scroll truncation.
    def progressive_scroll_and_capture(self, max_scrolls=None):
        """Collect to a verified end through the shared service; optional limits remain explicit."""
        # Avoid import cycles between adapters and the traversal service.
        from services.extraction import collect_page
        # Use a caller-supplied limit only as explicit bounded extraction, never completeness.
        return collect_page(self, "body", step_limit=max_scrolls)["screenshots"]
