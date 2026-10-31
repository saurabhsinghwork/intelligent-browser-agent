"""Resolve the user's installed Google Chrome instead of downloading another browser."""
# Inspect ordinary local installation paths independently of browser profiles.
from pathlib import Path
# Read standard installation roots without logging unrelated environment values.
import os
# Match executable discovery to the current operating system.
import sys
# Support installed Chrome on Unix PATHs.
import shutil


# Resolve the actual installed Google Chrome executable for the selected executor.
def installed_chrome():
    """Return a verified existing Chrome binary or an explicit setup error."""
    # Windows installations may be registered per-user or per-machine.
    candidates = []
    # Registry paths identify the installed application without reading browser data.
    if sys.platform == "win32":
        # Keep registry imports off non-Windows runtimes.
        import winreg
        # Check only the public Chrome application-path registration.
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            # Missing registration is ordinary on portable or per-user installations.
            try:
                # Read only the installed executable location.
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                    # Preserve the actual registered binary path.
                    candidates.append(Path(winreg.QueryValue(key, None)))
            # Continue to other documented installation locations.
            except OSError:
                # This is not permission to substitute Chromium or a different executor.
                pass
        # Standard Google Chrome locations cover nonregistered installations.
        for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            # Missing roots simply provide no candidate.
            if os.environ.get(variable):
                # No personal profile or credentials are read.
                candidates.append(Path(os.environ[variable]) / "Google" / "Chrome" / "Application" / "chrome.exe")
    # macOS Chrome has a stable installed application binary.
    elif sys.platform == "darwin":
        # Use the user's installed application.
        candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    # Linux installations publish their binary on PATH.
    else:
        # Avoid selecting chromium when the request explicitly calls for Google Chrome.
        executable = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        # Preserve only a real discovered executable.
        if executable:
            # Normalize it for the low-level Browser Use constructor.
            candidates.append(Path(executable))
    # Select only an existing executable from actual installation evidence.
    for candidate in candidates:
        # A nonexistent registration must not launch a guessed path.
        if candidate.is_file():
            # Return the concrete installed binary independently of profile storage.
            return str(candidate.resolve())
    # Make the actual missing requirement clear instead of silently downloading another browser.
    raise RuntimeError("Google Chrome is not installed or could not be located")
