"""Prove headed browsers remain visible when their host starts on a private desktop.

The parent creates a private test desktop without switching the user's desktop.
The child launches the actual selected adapter; its browser must appear on the
real input desktop and its pointer must already be visible before any task click.
"""
# Handle explicit parent/child diagnostic arguments.
import sys
# Resolve controlled fixture and application paths.
from pathlib import Path
# Launch the diagnostic child with explicit Windows startup desktop settings.
import subprocess
# Preserve virtual-environment imports when bypassing the Windows Python redirector.
import os
# Allocate a unique private host desktop that cannot conflict with another test.
from uuid import uuid4
# Serve only local synthetic browser content.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Bind the controlled fixture root without changing the working directory.
from functools import partial
# Keep the fixture responsive during browser operations.
from threading import Thread
# Resolve actual application imports for direct diagnostic execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Test actual selected executor behavior without model credentials.
from services.run_controller import create_browser_adapter
# Inspect native input-desktop visibility independently from the launch flag.
from browser.windows_desktop import _api, visible_browser_windows, desktop_command
# Resolve only this diagnostic's isolated real browser profile.
from browser.session_manager import session_path


# Execute inside a deliberately invisible host desktop.
def child(method):
    """Require a real native browser window and pointer on the user's visible desktop."""
    # Load the exact typed desktop APIs used by the application.
    ctypes, w, user, callback = _api()
    # Read the child's own desktop to prove the hidden-host reproduction is real.
    user.GetThreadDesktop.restype = w.HANDLE
    # Current thread IDs are DWORD values on Windows.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    # Read only this child's desktop name.
    handle = user.GetThreadDesktop(kernel.GetCurrentThreadId())
    # Allocate a native UTF-16 desktop name buffer.
    name, needed = ctypes.create_unicode_buffer(512), w.DWORD()
    # A native name query must succeed before this can count as a reproduction.
    assert user.GetUserObjectInformationW(handle, 2, name, ctypes.sizeof(name), ctypes.byref(needed))
    # Confirm the actual host is private rather than the user's Default desktop.
    assert name.value.startswith("IBAVisibilityTest-"), name.value
    # Serve only deterministic local content.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Keep responses available while the selected executor performs native input.
    Thread(target=server.serve_forever, daemon=True).start()
    # Isolate this local origin and method from every other profile.
    site = f"http://127.0.0.1:{server.server_port}/controlled.html"
    # Instantiate one actual executor, never a fake or another automation method.
    adapter = create_browser_adapter(method)
    # Always release the diagnostic's own browser and HTTP resources.
    try:
        # The adapter must override the host's private desktop for this visible launch.
        adapter.initialize(site, True)
        # Verify actual HWND geometry on the input desktop rather than a screenshot alone.
        windows = visible_browser_windows(session_path(site, method))
        # A headed flag or working CDP session cannot satisfy native visibility.
        assert windows, "No owned browser window on the actual input desktop"
        # Observation installs the passive pointer and dispatches its initial native movement.
        adapter.observe()
        # Read only the marker's actual resulting position.
        pointer = adapter._evaluate("() => {const box=document.getElementById('iba-cursor').getBoundingClientRect();return {x:box.left,y:box.top};}")
        # A read-only task must not leave its cursor at the old invisible negative position.
        assert pointer["x"] >= 0 and pointer["y"] >= 0, pointer
        # Record native proof without unrelated window titles or user information.
        print({"method": method, "private_host": name.value, "visible_on_input_desktop": True, "native_windows": len(windows), "cursor_visible_before_task_click": True})
    # Tests must not leave a visible or private browser behind.
    finally:
        # Close only this selected executor's owned browser.
        adapter.close_or_detach()
        # Normal cleanup must also close the actual visible browser frame.
        assert not visible_browser_windows(session_path(site, method)), "Owned browser window remained after normal cleanup"
        # Stop the private fixture service.
        server.shutdown()
        # Release its loopback socket.
        server.server_close()


# Host a diagnostic child on a new private desktop without changing the person's screen.
def main():
    """Reproduce hidden-host inheritance while verifying actual visible browser placement."""
    # Use the user-reported method by default.
    method = sys.argv[1] if len(sys.argv) > 1 else "playwright_mcp"
    # Load typed Win32 APIs only for this explicit Windows test.
    ctypes, w, user, callback = _api()
    # Preserve native pointer-width desktop handles.
    user.CreateDesktopW.restype = w.HANDLE
    # Describe arguments to avoid implicit pointer truncation.
    user.CreateDesktopW.argtypes = [w.LPCWSTR, w.LPCWSTR, w.LPVOID, w.DWORD, w.DWORD, w.LPVOID]
    # Allocate a private test host desktop without ever calling SwitchDesktop.
    name = "IBAVisibilityTest-" + uuid4().hex
    # Give only this test enough access to launch its own diagnostic child.
    desktop = user.CreateDesktopW(name, None, None, 0, 0xF01FF, None)
    # Creation must succeed before interpreting any browser result.
    assert desktop, "Could not create private diagnostic desktop"
    # Keep desktop cleanup independent of the child test outcome.
    try:
        # Reproduce the exact startup inheritance defect in the host process.
        startup = subprocess.STARTUPINFO()
        # The child's browser must escape this private host through the application's fix.
        startup.lpDesktop = "WinSta0\\" + name
        # Child mode launches a real selected browser without any model key.
        # The venv redirector may itself inherit a different desktop; launch the actual interpreter.
        environment = os.environ.copy()
        # Match Windows multiprocessing's supported virtual-environment bootstrap.
        environment["__PYVENV_LAUNCHER__"] = sys.executable
        # The native helper consumes Python bootstrap variables; preserve the test dependency path explicitly.
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / ".venv" / "Lib" / "site-packages")
        # Capture the private child's actual diagnostics because it has no console window.
        process = subprocess.run(desktop_command([sys._base_executable, "-B", str(Path(__file__).resolve()), method, "--child"], "WinSta0\\" + name), env=environment, startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=100)
        # Surface real failure evidence without hiding it behind the private desktop.
        print(process.stdout)
        # Propagate any real visibility or pointer failure to this diagnostic's exit status.
        assert process.returncode == 0, process.returncode
    # Release the private desktop only after the child/browser cleanup completes.
    finally:
        # Close only this test-created native desktop handle.
        user.CloseDesktop(desktop)


# Windows child imports must not recursively launch the test harness.
if __name__ == "__main__":
    # Child execution performs the actual hidden-host browser reproduction.
    if "--child" in sys.argv:
        # Preserve the selected actual method across the private desktop boundary.
        child(sys.argv[1])
    # Parent execution creates only the owned private test host desktop.
    else:
        # Run this explicit real-browser diagnostic.
        main()
