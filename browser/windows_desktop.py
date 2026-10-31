"""Launch owned browsers on the user's visible Windows desktop and verify their windows.

A server started on a private automation desktop can launch a genuinely headed
browser that the user cannot see. An owned native desktop launcher fixes desktop
inheritance without monkeypatching CreateProcess or switching the user's desktop.
"""
# Detect Windows without loading platform APIs on other operating systems.
import sys
# Build per-process launch options without replacing global subprocess behavior.
import subprocess
# Bound visibility checks during startup.
import time
# Resolve only the selected method's managed browser profile.
from pathlib import Path


# Load typed Win32 functions only when a Windows visibility operation needs them.
def _api():
    """Return user32 and its typed desktop-window enumeration callback."""
    # Keep Windows-only imports lazy for portable tests and headless execution.
    import ctypes
    # Use native pointer-width types for desktop and window handles.
    from ctypes import wintypes as w
    # Preserve Win32 failure codes for actionable launch diagnostics.
    user = ctypes.WinDLL("user32", use_last_error=True)
    # Describe the native callback signature on both 32-bit and 64-bit Windows.
    callback = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    # A desktop handle must never be truncated to a 32-bit integer.
    user.OpenInputDesktop.restype = w.HANDLE
    # Open only the desktop currently displayed to the person.
    user.OpenInputDesktop.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    # Resolve its actual name instead of assuming the launching thread's private desktop.
    user.GetUserObjectInformationW.argtypes = [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)]
    # Enumerate only windows belonging to that concrete visible desktop.
    user.EnumDesktopWindows.argtypes = [w.HANDLE, callback, w.LPARAM]
    # Match windows to their proved browser processes.
    user.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
    # Distinguish real browser frames from hidden message/helper windows in the same process.
    user.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
    # Read native top-level window styles without pointer truncation.
    user.GetWindowLongW.argtypes = [w.HWND, ctypes.c_int]
    # Restore/focus only the explicitly requested owned browser frame.
    user.SetForegroundWindow.argtypes = [w.HWND]
    # Read real visible-window geometry.
    user.GetWindowRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
    # Test actual native visibility rather than a headless configuration flag.
    user.IsWindowVisible.argtypes = [w.HWND]
    # Restore only this application's matched browser window asynchronously.
    user.ShowWindowAsync.argtypes = [w.HWND, ctypes.c_int]
    # Release only handles this helper explicitly opened.
    user.CloseDesktop.argtypes = [w.HANDLE]
    # Return the loaded API with its compatible type definitions.
    return ctypes, w, user, callback


# Supply desktop selection only to the process launched for the selected browser.
def browser_launch_options(headful):
    """Return explicit interactive-desktop launch options for a visible Windows browser."""
    # Headless and non-Windows runs retain normal subprocess behavior.
    if sys.platform != "win32" or not headful:
        # Do not move background execution onto an interactive desktop.
        return {}
    # The native command wrapper supplies the desktop; this flag hides only helper consoles.
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


# Build a native desktop-aware command because Python omits lpDesktop in subprocess startup.
def desktop_command(command, desktop):
    """Wrap one owned argument vector in the process-local native desktop launcher."""
    # The helper imports only standard-library modules, so the actual interpreter is sufficient.
    return [sys._base_executable, "-B", str(Path(__file__).with_name("desktop_launcher.py")), desktop, *command]


# Select the displayed desktop for this concrete headful browser command.
def browser_command(command, headful):
    """Route only visible Windows browser launches through the native desktop helper."""
    # Preserve the original executable vector for headless and non-Windows processes.
    if sys.platform != "win32" or not headful:
        # No helper or desktop override is needed for background execution.
        return command
    # Query the currently displayed desktop without switching it.
    ctypes, w, user, callback = _api()
    # Read its name through a handle opened only for this launch.
    desktop = user.OpenInputDesktop(0, False, 0x41)
    # Do not silently place an explicitly headed task on a hidden desktop.
    if not desktop:
        # Stop before launching an invisible GUI process.
        raise RuntimeError("Cannot access the visible Windows desktop")
    # Release the desktop query handle independently of process launch.
    try:
        # Keep the complete native desktop name.
        name, needed = ctypes.create_unicode_buffer(512), w.DWORD()
        # Resolve UOI_NAME through its typed API.
        if not user.GetUserObjectInformationW(desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed)):
            # Expose a real launch configuration failure.
            raise RuntimeError("Cannot resolve the visible Windows desktop")
        # The native helper forwards this actual field to CreateProcessW.
        return desktop_command(command, "WinSta0\\" + name.value)
    # The helper process does not inherit this query handle.
    finally:
        # Close only the desktop handle opened here.
        user.CloseDesktop(desktop)


# Prove that the selected browser owns a visible window on the user's actual desktop.
def visible_browser_windows(profile, restore=False):
    """Return native-window proof for only the exact managed browser profile."""
    # Other platforms need their platform-native window verification separately.
    if sys.platform != "win32":
        # This helper never invents Win32 proof on another operating system.
        return []
    # Inspect process arguments only to identify this exact application-managed profile.
    import psutil
    # Normalize the exact absolute owned profile, preserving its full directory boundary.
    expected = str(Path(profile).resolve()).lower().replace("\\", "/")
    # Retain only browser process identities matching that explicit launch argument.
    owned = set()
    # Inspect metadata without printing unrelated command lines or user data.
    for process in psutil.process_iter(["pid", "cmdline"]):
        # Process exit races are ordinary while launch is settling.
        try:
            # Match this browser's explicit user-data-dir rather than executable names.
            if any(argument.lower().replace("\\", "/").rstrip("/") == "--user-data-dir=" + expected for argument in process.info["cmdline"] or []):
                # Only these concrete browser owners may have their windows restored.
                owned.add(process.pid)
        # Unrelated inaccessible processes are outside this application's authority.
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Continue checking only the explicit managed profile.
            continue
    # Load the typed desktop/window APIs.
    ctypes, w, user, callback = _api()
    # Enumerate the user's current desktop, which may differ from this Python thread.
    desktop = user.OpenInputDesktop(0, False, 0x41)
    # Do not claim visible operation without access to the displayed desktop.
    if not desktop:
        # The caller will fail visibly after its bounded startup deadline.
        return []
    # Collect concrete visible windows without reading unrelated window titles.
    windows = []

    # Match one enumerated native window against the owned browser inventory.
    def inspect_window(hwnd, parameter):
        """Restore/check only an owned browser and retain visible geometry proof."""
        # Resolve this actual window's owning process.
        pid = w.DWORD()
        # Window ownership is independent of the screenshot/CDP connection.
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        # Ignore every unrelated application window.
        if pid.value not in owned:
            # Continue enumeration without modifying that window.
            return True
        # Chromium also owns invisible utility windows; do not show those to the user.
        class_name = ctypes.create_unicode_buffer(256)
        # Read only class metadata, never another application's title or contents.
        user.GetClassNameW(hwnd, class_name, 256)
        # Real decorated browser frames carry a native caption and system menu.
        style = user.GetWindowLongW(hwnd, -16)
        # Ignore hidden message windows even when their process owns the correct profile.
        if not class_name.value.startswith("Chrome_WidgetWin") or not style & 0xC00000 or not style & 0x80000:
            # These utility windows must remain untouched.
            return True
        # A requested visible browser should not remain hidden or minimized.
        if restore:
            # SW_RESTORE affects only the proved profile-owned browser window.
            user.ShowWindowAsync(hwnd, 9)
            # Request foreground display for this launch without controlling the OS mouse.
            user.SetForegroundWindow(hwnd)
        # Measure the actual native window after restoration.
        rectangle = w.RECT()
        # A visible GUI window must have meaningful display area.
        if user.IsWindowVisible(hwnd) and user.GetWindowRect(hwnd, ctypes.byref(rectangle)) and rectangle.right - rectangle.left > 100 and rectangle.bottom - rectangle.top > 100:
            # Keep only safe ownership/geometry proof, never window contents or titles.
            windows.append({"pid": pid.value, "hwnd": int(hwnd), "width": rectangle.right - rectangle.left, "height": rectangle.bottom - rectangle.top})
        # Inspect remaining owned windows without stopping at a decorative helper.
        return True

    # Keep the native callback alive throughout the synchronous enumeration.
    handler = callback(inspect_window)
    # Release the desktop handle on success and on enumeration failure.
    try:
        # Enumerating the input desktop proves the browser is on the user's displayed desktop.
        user.EnumDesktopWindows(desktop, handler, 0)
    # Never leak native handles between launches.
    finally:
        # Release only the handle created by this visibility check.
        user.CloseDesktop(desktop)
    # Return concrete native-window evidence for the chosen managed browser.
    return windows


# Give a headed launch a short opportunity to create its real native window.
def require_visible_browser(profile, cancelled=None, timeout=12):
    """Restore and verify the owned window, or fail instead of silently running invisibly."""
    # Preserve normal non-Windows behavior without fabricating Win32 evidence.
    if sys.platform != "win32":
        # The browser runtime still enforces the selected headful flag on other systems.
        return []
    # Bound startup verification independently of model request timing.
    deadline = time.monotonic() + timeout
    # Wait only for this browser's real window to appear on the visible desktop.
    while time.monotonic() < deadline:
        # Stop may interrupt launch verification before another visibility query.
        if cancelled is not None and cancelled.is_set():
            # Do not continue a browser task after cancellation.
            raise InterruptedError("Stopped while waiting for the visible browser")
        # Restore only the matched browser, then inspect real native-window visibility.
        windows = visible_browser_windows(profile, restore=True)
        # A real native window is required before any model action begins.
        if windows:
            # Return safe proof for monitoring and practical tests.
            return windows
        # Avoid busy looping while the browser finishes creating its native window.
        time.sleep(0.1)
    # Expose a concrete startup error rather than doing a hidden headed run.
    raise RuntimeError("Visible browser window was not found on the interactive Windows desktop; task stopped")


# Keep historical imports compatible without a process-wide desktop monkeypatch.
def attach_to_interactive_desktop():
    """Return explicit launch options; do not alter unrelated threads or process APIs."""
    # Modern callers pass these options only to their owned browser launcher.
    return browser_launch_options(True)


# Historical setup callers must not replace global CreateProcess behavior.
def setup_windows_desktop_patch():
    """Leave process creation untouched; per-launch options handle visible browsers."""
    # No global monkeypatch is needed or installed.
    return None
