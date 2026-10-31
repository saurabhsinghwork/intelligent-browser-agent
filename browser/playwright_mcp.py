"""Pinned stdio Playwright MCP transport with deadlines and scoped ownership.

MCP executes all browser code and screenshots. A background reader prevents blocking
readline calls from hiding Stop indefinitely. No direct Playwright fallback exists.
"""
# Encode the MCP JSON-RPC protocol and browser configuration.
import json
# Resolve launchers and spawn the one owned server process.
import shutil
# Own the pinned local server process and its protocol pipes.
import subprocess
# Launch owned browser helpers on the actual visible Windows desktop when requested.
from browser.windows_desktop import browser_launch_options, browser_command, require_visible_browser
# Consume protocol lines with cancellable bounded queue waits.
from queue import Queue, Empty
# Read protocol output independently without blocking the graph thread.
from threading import Thread, RLock
# Track per-request deadlines rather than a fixed task-duration limit.
import time
# Reuse common policy, stable targeting, observation, and typed-result normalization.
from browser.base import BaseBrowserAdapter, decode_result
# Preserve isolated reusable browser profiles.
from browser.session_manager import ensure_session_dir


# Implement actual MCP transport behind the shared browser behavior.
class PlaywrightMCPAdapter(BaseBrowserAdapter):
    """Own one pinned MCP server, one browser profile, and sequential request stream."""

    # Allow injected MCP clients for deterministic protocol contract tests.
    def __init__(self, client=None, command=None):
        """Prepare transport state without starting Node or opening Chrome."""
        # Allocate shared run state and immutable artifact directory.
        super().__init__()
        # Allow fake transport injection without changing live execution semantics.
        self.client = client
        # Pin the exact server version instead of downloading whatever latest means.
        self.command = command or ["npx", "--yes", "--prefer-offline", "@playwright/mcp@0.0.83"]
        # Retain only the server this adapter owns.
        self._process = None
        # Read stdout asynchronously into a cancellable queue.
        self._messages = Queue()
        # Keep JSON-RPC IDs unique within this connection.
        self._request_id = 0
        # Serialize access to the single protocol stream.
        self._lock = RLock()
        # Discover the pinned server's actual name for its application-owned code tool.
        self._code_tool = "browser_run_code"
        # Cleanup must remain possible without clearing the shared cancellation signal.
        self._closing = False

    # Read protocol messages without blocking the thread running graph nodes.
    def _read_messages(self, process, messages):
        """Queue stdout lines and a terminal sentinel when the owned server exits."""
        # The transport thread only reads its own server's stdout.
        for line in process.stdout:
            # Preserve each complete line for matching JSON-RPC response IDs.
            messages.put(line)
        # Wake any pending request promptly when the pipe closes.
        messages.put(None)

    # Send one bounded JSON-RPC request.
    def _request(self, method, params):
        """Return the matching result or raise on Stop, protocol error, EOF, or deadline."""
        # Allocate a unique ID so notifications cannot be mistaken for results.
        self._request_id += 1
        # Retain the ID while unrelated notifications arrive.
        identifier = self._request_id
        # Serialize one discrete MCP protocol message.
        message = {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
        # Send newline-delimited JSON to the owned server.
        self._process.stdin.write(json.dumps(message) + "\n")
        # Flush immediately so the request cannot remain buffered during cancellation waits.
        self._process.stdin.flush()
        # Bound each request independently of how long the overall task may run.
        deadline = time.monotonic() + (3 if self._closing else 45)
        # Ignore notifications until the matching response arrives.
        while time.monotonic() < deadline:
            # Check Stop between short queue reads.
            # A cancelled run may still close its owned browser normally.
            if not self._closing:
                # All ordinary tool requests remain promptly cancellable.
                self.check_cancelled()
            # Wait briefly rather than calling blocking stdout.readline in the graph thread.
            try:
                # A short wait keeps cancellation observable.
                line = self._messages.get(timeout=0.1)
            # A live server may still be completing its tool call.
            except Empty:
                # Repeat the deadline and cancellation checks.
                continue
            # A closed stream is a concrete transport failure.
            if line is None:
                # Do not loop indefinitely after a Node/server crash.
                raise RuntimeError("Playwright MCP closed its output stream")
            # Ignore launcher diagnostics that are not JSON-RPC messages.
            try:
                # Decode protocol data without evaluating text.
                response = json.loads(line)
            # npx may emit a readable startup message.
            except json.JSONDecodeError:
                # Keep waiting within the same explicit request deadline.
                continue
            # Notifications are not the matching requested result.
            if response.get("id") != identifier:
                # Skip server notifications without changing request accounting.
                continue
            # Surface JSON-RPC errors distinctly from successful tool results.
            if "error" in response:
                # Bound the diagnostic without leaking a full request payload.
                raise RuntimeError("MCP protocol error: " + str(response["error"])[:500])
            # Return the actual server result.
            return response.get("result", {})
        # A tool that never responds must not make Stop unavailable forever.
        raise TimeoutError("Playwright MCP request timed out")

    # Normalize actual MCP content blocks and readable tool-result wrappers.
    def _call(self, name, arguments=None):
        """Call one advertised MCP tool and reject isError results."""
        # Keep one request at a time on the shared protocol stream.
        with self._lock:
            # Choose an injected test client only when explicitly provided.
            result = self.client.call_tool(name, arguments or {}) if self.client else self._request("tools/call", {"name": name, "arguments": arguments or {}})
        # Explicit injected transports may already return normalized lists or scalars.
        if not isinstance(result, dict):
            # Preserve typed tab lists without assuming every result is a mapping.
            return decode_result(result)
        # Tool-reported failures are not successful browser actions.
        if result.get("isError"):
            # Retain a bounded readable diagnostic.
            raise RuntimeError("MCP tool failed: " + str(result.get("content", []))[:700])
        # Prefer structured tool results when the server supplies them.
        if result.get("structuredContent") is not None:
            # Normalize scalar string/Boolean differences consistently.
            return decode_result(result["structuredContent"])
        # Parse readable content only when actual content blocks are present.
        if "content" in result:
            # Ignore binary image blocks here; screenshots are saved by the screenshot tool.
            text = "\n".join(item.get("text", "") for item in result["content"] if item.get("type") == "text")
            # Extract Result without treating tool transcript prose as source evidence.
            return decode_result(text)
        # Keep already normalized injected-client responses intact.
        return decode_result(result)

    # Start the pinned server and negotiate its actual tool contract.
    def initialize(self, site, headful, session_reference=None):
        """Launch MCP with a persistent Chrome profile, then guard and navigate."""
        # A resumed visibility transfer starts a fresh protocol stream.
        self._messages = Queue()
        # Restore normal cancellation after the previous runtime's cleanup.
        self._closing = False
        # Preserve run-scoped grants passed before initialization.
        self.set_site(site, headful)
        # Isolate browser storage by website and selected execution method.
        profile = ensure_session_dir(site, "playwright_mcp").resolve()
        # Start a real server only when no test transport was injected.
        if self.client is None:
            # Configure Chrome and deterministic viewport through the supported server config.
            configuration = {"browser": {"browserName": "chromium", "userDataDir": str(profile), "launchOptions": {"channel": "chrome", "headless": not headful, "args": ["--test-type", "--disable-infobars"]}, "contextOptions": {"viewport": {"width": 1280, "height": 800}, "serviceWorkers": "block"}}}
            # Keep transient launch configuration separate from provider credentials.
            path = profile / "iba_mcp.json"
            # Write only browser options, never an API key.
            path.write_text(json.dumps(configuration), encoding="utf-8")
            # Resolve npx's Windows launcher when necessary.
            executable = shutil.which(self.command[0]) or shutil.which(self.command[0] + ".cmd")
            # Fail explicitly if the selected method's runtime is missing.
            if not executable:
                # Explain the actual missing dependency.
                raise RuntimeError("Node.js/npx is required for Playwright MCP")
            # Launch only the owned pinned MCP process.
            self._process = subprocess.Popen(browser_command([executable, *self.command[1:], "--config", str(path)], headful), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", bufsize=1, **browser_launch_options(headful))
            # Start the protocol reader before sending initialize.
            Thread(target=self._read_messages, args=(self._process, self._messages), daemon=True, name="iba-mcp-reader").start()
            # Negotiate the MCP protocol explicitly.
            self._request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "intelligent-browser-agent", "version": "0.2.0"}})
            # Complete the protocol's initialized notification.
            self._process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
            # Ensure the notification reaches the server before tools are requested.
            self._process.stdin.flush()
            # Inspect actual server tools instead of assuming a stale contract.
            tools = self._request("tools/list", {})
            # Require deterministic evaluation and native-code tools used by this adapter.
            names = {item["name"] for item in tools["tools"]}
            # This pinned version names its trusted local-code endpoint explicitly unsafe.
            self._code_tool = "browser_run_code" if "browser_run_code" in names else "browser_run_code_unsafe"
            # Only version-controlled application code is ever sent to this endpoint.
            if not {self._code_tool, "browser_evaluate", "browser_take_screenshot"}.issubset(names):
                # An incompatible server cannot silently substitute another method.
                raise RuntimeError("Pinned MCP server lacks required browser capabilities")
        # Open an empty tab so guards precede the selected site's first navigation.
        self._call("browser_navigate", {"url": "about:blank"})
        # Bring the browser window onto the visible desktop immediately so user sees it right away.
        if headful and self.client is None:
            # Check the actual profile-owned native window on the interactive desktop.
            require_visible_browser(profile, self.stop_event)
            # Publish that visibility was verified before waiting on destination navigation.
            if self.monitor is not None:
                # Notify UI that visible window is active.
                self.monitor.update_status("Visible browser window verified on the interactive desktop")
        # A headed setup operation installs policy and the cursor before destination navigation.
        self.install_visible_cursor()
        # Follow server redirects only through the shared authorization guard.
        # Restore explicitly transferred authentication before any destination script executes.
        self.restore_transfer()
        # Navigate only after policy and eligible session state are installed.
        self._native("navigate", site)
        # Ensure visible cursor is immediately rendered on the navigated page.
        if headful:
            # Render pointer overlay on navigated destination.
            self.install_visible_cursor()

    # Evaluate application-owned page inspection functions.
    def _evaluate(self, source):
        """Use browser_evaluate with its advertised function argument."""
        # No provider-generated code is accepted by this transport.
        return self._call("browser_evaluate", {"function": source})

    # Execute native Playwright operations through MCP's documented tool.
    def _run_code(self, source):
        """Use browser_run_code while retaining MCP as the sole executor."""
        # The function source is assembled only from version-controlled application scripts.
        return self._call(self._code_tool, {"code": source})

    # Save immutable viewport evidence through MCP.
    def _screenshot(self, path):
        """Request a CSS-scale viewport screenshot and return its intended local path."""
        # Save rather than printing inline binary image content.
        self._call("browser_take_screenshot", {"filename": str(path), "fullPage": False, "scale": "css"})
        # The shared observer verifies file existence.
        return str(path)

    # Use the real context's tab inventory.
    def manage_tabs(self):
        """Return current tab metadata from the MCP-owned context."""
        # Native code reads actual context pages.
        return self._native("tabs")

    # Dispatch a validated browsing key through the official keyboard tool.
    def _press(self, key):
        """Press one permitted key; subsequent observation verifies its effect."""
        # Preserve the server's documented key argument.
        self._call("browser_press_key", {"key": key})
        # Do not claim task completion from a keyboard transport result.
        return {"success": True, "action": "press"}

    # Use MCP tab operations rather than manipulating another browser connection.
    def _tab_action(self, kind, target):
        """Validate a current tab index and select/close it through MCP."""
        # Reject unknown or nonnumeric tab references.
        if not str(target).isdigit() or int(target) >= len(self.manage_tabs()):
            # Re-observation can recover from a closed tab.
            raise LookupError("Unknown browser tab")
        # Select the operation supported by the official server.
        self._call("browser_tabs", {"action": "select" if kind == "switch_tab" else "close", "index": int(target)})
        # The graph then verifies the active browser state.
        return {"success": True, "action": kind}

    # Terminate only the server process this adapter owns.
    def close_or_detach(self):
        """Release MCP/browser resources while preserving eligible profile data."""
        # Injected clients own their own lifecycle.
        if self.client is None and self._process and self._process.poll() is None:
            # Ask the owned browser to close before terminating the wrapper.
            try:
                # A short protocol close saves eligible session state normally.
                self._closing = True
                # Close through the selected method rather than a global process kill.
                self._call("browser_close")
            # Transport failures must not replace the primary task outcome.
            finally:
                # Stop only the owned server.
                self._process.terminate()
                # Bound cleanup even if Node does not terminate normally.
                try:
                    # Reap the process and close its pipes.
                    self._process.wait(timeout=3)
                # Escalate only for this adapter's process.
                except subprocess.TimeoutExpired:
                    # The supervisor separately owns any remaining descendant cleanup.
                    self._process.kill()
