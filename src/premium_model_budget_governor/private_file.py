"""Create private local secret files before writing, then replace atomically."""
import os
from pathlib import Path
import secrets


def _windows_fd(path):
    import ctypes as c
    from ctypes import wintypes as w
    import msvcrt

    kernel = c.WinDLL("kernel32", use_last_error=True)
    security = c.WinDLL("advapi32", use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.LocalFree.argtypes = [c.c_void_p]
    security.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)]
    security.GetTokenInformation.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
    security.ConvertSidToStringSidW.argtypes = [c.c_void_p, c.POINTER(w.LPWSTR)]
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [w.LPCWSTR, w.DWORD, c.POINTER(c.c_void_p), c.POINTER(w.DWORD)]
    class Attributes(c.Structure):
        _fields_ = [("nLength", w.DWORD), ("lpSecurityDescriptor", c.c_void_p), ("bInheritHandle", w.BOOL)]
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.POINTER(Attributes), w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    token, sid_text, descriptor = w.HANDLE(), w.LPWSTR(), c.c_void_p()
    try:
        if not security.OpenProcessToken(kernel.GetCurrentProcess(), 8, c.byref(token)):
            raise c.WinError(c.get_last_error())
        size = w.DWORD()
        security.GetTokenInformation(token, 1, None, 0, c.byref(size))
        if not size.value:
            raise c.WinError(c.get_last_error())
        buffer = c.create_string_buffer(size.value)
        if not security.GetTokenInformation(token, 1, buffer, size, c.byref(size)):
            raise c.WinError(c.get_last_error())
        sid = c.cast(buffer, c.POINTER(c.c_void_p))[0]
        if not security.ConvertSidToStringSidW(sid, c.byref(sid_text)):
            raise c.WinError(c.get_last_error())
        # Protected DACL: only the process user's SID receives file access.
        sddl = "D:P(A;;FA;;;" + sid_text.value + ")"
        if not security.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, c.byref(descriptor), None):
            raise c.WinError(c.get_last_error())
        attributes = Attributes(c.sizeof(Attributes), descriptor, False)
        handle = kernel.CreateFileW(str(path), 0x40000000, 0, c.byref(attributes), 1, 0x80, None)
        if handle == c.c_void_p(-1).value:
            raise c.WinError(c.get_last_error())
        try:
            return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
        except Exception:
            kernel.CloseHandle(handle)
            raise
    finally:
        if descriptor:
            kernel.LocalFree(descriptor)
        if sid_text:
            kernel.LocalFree(c.cast(sid_text, c.c_void_p))
        if token:
            kernel.CloseHandle(token)


def write_private(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name("." + path.name + "." + secrets.token_hex(12))
    created = False
    try:
        fd = _windows_fd(temporary) if os.name == "nt" else os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if created:
            temporary.unlink(missing_ok=True)


def remove_if_unchanged(path: Path, expected: bytes):
    try:
        if path.is_symlink():
            return
        with path.open("rb") as stream:
            content = stream.read(len(expected) + 1)
        if content == expected:
            path.unlink(missing_ok=True)
    except FileNotFoundError:
        pass
