"""Pinned Playwright CLI transport for the shared browser contract.

All browser work goes through the actual CLI. Trusted scripts are loaded from files
to avoid Windows command-length limits; no direct Playwright fallback is used.
"""
# Serialize CLI results and per-session browser configuration.
import json
# Resolve the executable without shell command interpolation.
import shutil
# Launch only discrete argument arrays, never a shell-built browser command.
import subprocess
# Launch owned browser helpers on the actual visible Windows desktop when requested.
from browser.windows_desktop import browser_launch_options, browser_command, require_visible_browser
# Allocate temporary trusted script names within the run's artifact directory.
from uuid import uuid4
# Locate persisted session profiles independently of the current working directory.
from pathlib import Path
# Share policy, targeting, inspection, and result normalization.
from browser.base import BaseBrowserAdapter, decode_result, SCRIPT_ROOT
# Reuse the established session path convention.
from browser.session_manager import ensure_session_dir


# Implement only CLI transport and lifecycle; common behavior stays in the base.
class PlaywrightCLIAdapter(BaseBrowserAdapter):
    """Drive one isolated pinned CLI session in headful or headless Chrome."""

    # Accept an explicit executable override for controlled transport tests.
    def __init__(self, command=None, timeout=30):
        """Configure executable and per-call deadline without opening a browser."""
        # Allocate common run ownership, policy, and artifact state.
        super().__init__()
        # Default to the installed pinned CLI, not a runtime latest download.
        self.command = command or ["playwright-cli"]
        # Bound each individual command independently from overall task duration.
        self.timeout = timeout
        # Isolate browser sessions even for concurrent application sessions.
        self._session_name = "iba_" + self.run_id[:12]
        # Track whether normal cleanup must ignore a previously requested Stop.
        self._closing = False
        # Retain the active command process for interruption.
        self._process = None

    # Invoke the actual CLI using argument arrays and UTF-8 output.
    def _run(self, args):
        """Return parsed CLI output; raise on timeout, cancellation, or tool/process failure."""
        # Resolve Windows .cmd launchers and ordinary executables.
        executable = shutil.which(self.command[0]) or shutil.which(self.command[0] + ".cmd")
        # Fail explicitly rather than substituting another automation method.
        if not executable:
            # Keep missing-runtime guidance concrete.
            raise RuntimeError("Playwright CLI is missing; install @playwright/cli@0.1.22.")
        # Build a discrete argument list with an isolated session name.
        command = [executable, *self.command[1:], "-s=" + self._session_name, *args]
        # Start only the selected command with bounded, readable output.
        self._process = subprocess.Popen(browser_command(command, self.headful), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **browser_launch_options(self.headful))
        # Communicate with short waits so Stop is not hidden behind a long subprocess timeout.
        import time
        # Measure the command's own deadline.
        deadline = time.monotonic() + self.timeout
        # Continue until output is available or a bounded stop/error occurs.
        while True:
            # Cancel ordinary operations promptly while still permitting cleanup commands.
            if not self._closing and self.stop_event.is_set():
                # Terminate the owned command rather than touching unrelated browsers.
                self._process.kill()
                # Reap the command process and its pipes.
                self._process.communicate()
                # Let the controller retain partial evidence.
                raise InterruptedError("Stopped during CLI operation")
            # Enforce a concrete per-command timeout.
            if time.monotonic() >= deadline:
                # Stop only this owned CLI command.
                self._process.kill()
                # Drain pipes after termination.
                self._process.communicate()
                # Preserve a distinct timeout outcome for recovery.
                raise TimeoutError("Playwright CLI operation timed out")
            # Wait briefly for process output while keeping cancellation responsive.
            try:
                # communicate can be called again after a TimeoutExpired.
                stdout, stderr = self._process.communicate(timeout=0.1)
                # Leave the polling loop once the process has finished.
                break
            # A still-running command is expected during navigation or screenshots.
            except subprocess.TimeoutExpired:
                # Retry the bounded cancellation/deadline check.
                continue
        # Do not treat readable tool errors as success merely because the wrapper exited zero.
        if self._process.returncode or "### Error" in stdout:
            # Bound raw diagnostics and let the monitor redact secrets.
            raise RuntimeError("Playwright CLI failed: " + (stderr or stdout)[-1200:])
        # Prefer the raw JSON result while preserving a readable wrapper when necessary.
        return decode_result(stdout)

    # Load trusted scripts from a file so Windows launcher limits cannot truncate them.
    def _run_code(self, source):
        """Execute an application-owned Playwright function through CLI run-code."""
        # Keep scripts in the run-owned artifact directory.
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        # Use unique paths so overlapping diagnostic reads cannot overwrite an active script.
        path = self._screenshot_dir / ("command_" + uuid4().hex + ".js")
        # Write exact application-owned code as UTF-8.
        path.write_text(source, encoding="utf-8")
        # Load the file through the CLI's documented filename option.
        return self._run(["run-code", "--filename", str(path), "--raw"])

    # Map zero-argument page inspection into the same CLI-only transport.
    def _evaluate(self, source):
        """Evaluate a trusted page function and return its actual result."""
        # page.evaluate receives a function, not a string of provider-generated code.
        return self._run_code("async (page) => await page.evaluate(" + source + ")")

    # Capture immutable viewport evidence through the actual CLI.
    def _screenshot(self, path):
        """Save a viewport PNG to the requested absolute artifact path."""
        # Pass filenames as arguments rather than shell-built command strings.
        self._run(["screenshot", "--filename", str(path)])
        # The base verifies that the file actually exists before using it.
        return str(path)

    # Start one browser and install policy before navigation.
    def initialize(self, site, headful, session_reference=None):
        """Open an isolated persistent Chrome profile and navigate under exact-host guards."""
        # Preserve controller-supplied grants rather than erasing them.
        self.set_site(site, headful)
        # Isolate reusable sessions by selected site and method.
        profile = ensure_session_dir(site, "playwright_cli").resolve()
        # Open an empty tab first so website redirects cannot precede guard installation.
        arguments = ["open", "about:blank", "--browser", "chrome", "--persistent", "--profile", str(profile)]
        # Use the actual visible-browser option only when selected.
        if headful:
            # Keep the user's real browser window visible.
            arguments.append("--headed")
        # Launch through CLI rather than a hidden direct Playwright session.
        self._run(arguments)
        # Bring the browser window onto the visible desktop immediately so user sees it right away.
        if headful:
            # Force window restore and focus via Win32 APIs.
            require_visible_browser(profile, self.stop_event)
            # Update user interface monitor if available.
            if self.monitor is not None:
                # Notify UI that visible window is active.
                self.monitor.update_status("Visible browser window verified on the interactive desktop")
        # A headed setup operation installs policy and the cursor before destination navigation.
        self.install_visible_cursor()
        # Navigate using the same guarded implementation as subsequent actions.
        # Restore explicitly transferred authentication before any destination script executes.
        self.restore_transfer()
        # Navigate only after policy and eligible session state are installed.
        self._native("navigate", site)
        # Ensure visible cursor is immediately rendered on the navigated page.
        if headful:
            # Render pointer overlay on navigated destination.
            self.install_visible_cursor()

    # Inspect actual tabs through the selected CLI runtime.
    def manage_tabs(self):
        """Return real context pages and active flags."""
        # Native code reads context metadata without launching another method.
        return self._native("tabs")

    # Route keyboard input through the official CLI command.
    def _press(self, key):
        """Press one already validated browsing key."""
        # The base restricts keys before this transport is called.
        self._run(["press", key])
        # Verification still observes the resulting browser state.
        return {"success": True, "action": "press"}

    # Switch or close only explicitly identified existing tabs.
    def _tab_action(self, kind, target):
        """Validate tab indices and execute the corresponding CLI operation."""
        # Require a real listed index rather than silently choosing zero.
        if not str(target).isdigit() or int(target) >= len(self.manage_tabs()):
            # Let the agent re-observe a changed tab inventory.
            raise LookupError("Unknown browser tab")
        # Use the CLI's own active-tab machinery.
        self._run(["tab-select" if kind == "switch_tab" else "tab-close", str(target)])
        # A subsequent observation verifies the active context.
        return {"success": True, "action": kind}

    # Keep the readable metadata helper for existing integrations.
    @staticmethod
    def _extract_label(text, label):
        """Return a readable tool label's first value, or empty when absent."""
        # Inspect lines rather than depending on a particular YAML indentation.
        for line in text.splitlines():
            # Restrict extraction to the requested known metadata label.
            if label in line:
                # Remove formatting only from transport metadata, never source text.
                return line.split(label, 1)[1].strip().strip(chr(96) + chr(34) + chr(39))
        # Preserve absence rather than fabricating metadata.
        return ""

    # Close only this named session and retain its persistent profile.
    def close_or_detach(self):
        """Release the CLI-owned browser; do not delete sessions or use close-all."""
        # Permit cleanup even after cancellation was requested.
        self._closing = True
        # Attempt scoped cleanup without replacing the primary run outcome.
        try:
            # Closing the session persists its eligible reusable profile.
            self._run(["close"])
        # A failed cleanup remains a diagnostic rather than false task success.
        finally:
            # Restore ordinary cancellation behavior if the instance is inspected again.
            self._closing = False
