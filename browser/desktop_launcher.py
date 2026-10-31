"""Start one owned child on an explicit Windows desktop with inherited protocol pipes.

Python's subprocess.STARTUPINFO does not forward lpDesktop to CreateProcess.
This small process-local launcher uses the native structure directly; it does not
replace or monkeypatch Python's process APIs. Arguments contain no provider keys.
"""
# Parse the concrete desktop and owned child argument vector.
import sys
# Preserve the inherited environment and resolve cmd.exe for Windows command files.
import os
# Quote a discrete Windows argument vector correctly.
import subprocess
# Use actual pointer-width Win32 structures for native process startup.
import ctypes
# Keep native integer and handle fields compatible with Windows.
from ctypes import wintypes as w
# Expose inherited stdio pipe handles to the owned child.
import msvcrt


# Represent the complete native structure, including the desktop Python omits.
class StartupInfo(ctypes.Structure):
    """Match STARTUPINFOW so the exact owned launch reaches the requested desktop."""
    # Retain native field ordering and alignment, including reserved pointer fields.
    _fields_ = [("cb", w.DWORD), ("lpReserved", w.LPWSTR), ("lpDesktop", w.LPWSTR), ("lpTitle", w.LPWSTR), ("dwX", w.DWORD), ("dwY", w.DWORD), ("dwXSize", w.DWORD), ("dwYSize", w.DWORD), ("dwXCountChars", w.DWORD), ("dwYCountChars", w.DWORD), ("dwFillAttribute", w.DWORD), ("dwFlags", w.DWORD), ("wShowWindow", w.WORD), ("cbReserved2", w.WORD), ("lpReserved2", ctypes.POINTER(w.BYTE)), ("hStdInput", w.HANDLE), ("hStdOutput", w.HANDLE), ("hStdError", w.HANDLE)]


# Retain the exact child handles until its protocol process exits.
class ProcessInfo(ctypes.Structure):
    """Match PROCESS_INFORMATION without truncating process or thread handles."""
    # These fields belong only to the native child created by this launcher.
    _fields_ = [("hProcess", w.HANDLE), ("hThread", w.HANDLE), ("dwProcessId", w.DWORD), ("dwThreadId", w.DWORD)]


# Launch and wait for one explicitly requested owned browser/helper process.
def main():
    """Preserve pipe-based automation while choosing the actual child desktop."""
    # Require an explicit desktop followed by a concrete nonempty executable vector.
    desktop, arguments = sys.argv[1], sys.argv[2:]
    # Missing executable arguments must not become an implicit shell command.
    if not arguments:
        # Fail before creating a process with ambiguous ownership.
        raise ValueError("Desktop launcher requires an executable")
    # Load native process functions with useful last-error diagnostics.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    # Describe full native CreateProcessW pointer and string arguments.
    kernel.CreateProcessW.argtypes = [w.LPCWSTR, w.LPWSTR, w.LPVOID, w.LPVOID, w.BOOL, w.DWORD, w.LPVOID, w.LPCWSTR, ctypes.POINTER(StartupInfo), ctypes.POINTER(ProcessInfo)]
    # Preserve pointer-width native stdio handles.
    kernel.GetStdHandle.restype = w.HANDLE
    # Forward only explicitly inherited protocol handles.
    kernel.SetHandleInformation.argtypes = [w.HANDLE, w.DWORD, w.DWORD]
    # Native process waiting uses the exact owned process handle.
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    # Retrieve only that child's exit status.
    kernel.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    # Release only handles created by this launcher.
    kernel.CloseHandle.argtypes = [w.HANDLE]
    # Populate the actual native desktop field rather than a Python-only ignored attribute.
    startup = StartupInfo()
    # Windows requires the complete structure size.
    startup.cb = ctypes.sizeof(startup)
    # The requested interactive desktop is supplied only by trusted application launch code.
    startup.lpDesktop = desktop
    # Preserve stdin/stdout/stderr pipes used by MCP, CLI, and Browser Use.
    startup.dwFlags = 0x100
    # Retain fallback NUL descriptors until the child has inherited valid handles.
    descriptors = []
    # Resolve all three actual inherited standard handles.
    for field, identifier in (("hStdInput", -10), ("hStdOutput", -11), ("hStdError", -12)):
        # Native negative standard-stream constants use DWORD encoding.
        handle = kernel.GetStdHandle(w.DWORD(identifier & 0xFFFFFFFF))
        # Background hosts may lack a console stdin; provide an inherited NUL stream.
        if not handle or handle == ctypes.c_void_p(-1).value:
            # Open only the Windows null device, never a user file.
            descriptor = os.open(os.devnull, os.O_RDWR)
            # Keep the descriptor alive through process creation.
            descriptors.append(descriptor)
            # Resolve its real native handle for STARTUPINFO.
            handle = msvcrt.get_osfhandle(descriptor)
        # Mark the owned standard pipe inheritable for this concrete child.
        kernel.SetHandleInformation(handle, 1, 1)
        # Assign the exact native handle to the corresponding stream.
        setattr(startup, field, handle)
    # CMD files require cmd.exe; ordinary browser/Python executables launch directly.
    if arguments[0].lower().endswith((".cmd", ".bat")):
        # Resolve the installed Windows command interpreter without shell interpolation.
        executable = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        # Quote the complete argument vector inside cmd.exe's required outer command quotes.
        command = subprocess.list2cmdline([executable]) + ' /d /s /c "' + subprocess.list2cmdline(arguments) + '"'
    # Chrome and other executables accept the native argument vector directly.
    else:
        # Preserve the concrete executable identity independently of argument quoting.
        executable = arguments[0]
        # Use Python's Windows command-line quoting for embedded spaces and quotes.
        command = subprocess.list2cmdline(arguments)
    # Allocate the actual child process/thread handles.
    process = ProcessInfo()
    # Let CreateProcessW modify its command-line buffer as required.
    buffer = ctypes.create_unicode_buffer(command)
    # Create the child with inherited pipes and no helper console window.
    if not kernel.CreateProcessW(executable, buffer, None, None, True, 0x08000000, None, None, ctypes.byref(startup), ctypes.byref(process)):
        # Expose the real launch failure rather than continuing invisibly.
        raise ctypes.WinError(ctypes.get_last_error())
    # Process creation has copied the thread startup configuration.
    kernel.CloseHandle(process.hThread)
    # Always release the owned process and fallback stream handles.
    try:
        # Preserve the wrapper lifecycle until this exact child exits.
        kernel.WaitForSingleObject(process.hProcess, 0xFFFFFFFF)
        # Propagate actual tool failure to the controlling adapter.
        code = w.DWORD()
        # Read only the created child's exit code.
        kernel.GetExitCodeProcess(process.hProcess, ctypes.byref(code))
        # Keep process success/failure semantics identical to the original executor.
        return code.value
    # Native handles must not leak across repeated browser launches.
    finally:
        # Close only the process handle returned by this owned creation.
        kernel.CloseHandle(process.hProcess)
        # Release only fallback NUL streams opened above.
        for descriptor in descriptors:
            # Real inherited protocol pipes remain owned by their original subprocess machinery.
            os.close(descriptor)


# Importing this helper must never launch another process.
if __name__ == "__main__":
    # Exit with the actual owned child's status.
    sys.exit(main())
