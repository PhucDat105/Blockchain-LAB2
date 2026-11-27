"""
[T01 - Project Initialization]
Lớp tương thích đa nền tảng (Windows / macOS / Linux + Python 3.10..3.14 + OpenSSL 3.x)
dành cho thư viện `python-bitcoinlib`.

Vấn đề kỹ thuật giải quyết:
1. Trên Windows (Python 3.8+) và macOS (Homebrew OpenSSL 3), `ctypes.util.find_library('ssl')`
   trả về `None`, khiến `import bitcoin.wallet` ném lỗi `TypeError` khi nạp OpenSSL DLL.
   Module này tự động định vị `libcrypto*.dll` / `libcrypto*.dylib` / `libcrypto.so*` đi kèm Python/OS.
2. Trên một số bản Linux dùng OpenSSL 3.0 mặc định tắt legacy provider, `hashlib.new('ripemd160')`
   có thể bị vô hiệu hóa; module cung cấp fallback `RIPEMD-160` thuần Python chuẩn đặc tả để `Hash160`
   luôn hoạt động ổn định trên máy của cả 5 thành viên.
"""

import ctypes.util
import glob
import hashlib
import os
import struct
import sys
from typing import Optional

_PATCHED = False


def _find_bundled_libcrypto() -> Optional[str]:
    """Tìm đường dẫn thư viện động OpenSSL (`libcrypto`) sẵn có trong Python hoặc hệ điều hành."""
    candidates: list[str] = []

    # 1. Thư mục DLLs / Library/bin của Python trên Windows (venv & base python)
    for prefix in {sys.prefix, sys.base_prefix}:
        candidates.extend(glob.glob(os.path.join(prefix, "DLLs", "libcrypto*.dll")))
        candidates.extend(glob.glob(os.path.join(prefix, "Library", "bin", "libcrypto*.dll")))

    # 2. Đường dẫn Homebrew OpenSSL 3 trên macOS (Apple Silicon & Intel)
    candidates.extend(
        [
            "/opt/homebrew/opt/openssl@3/lib/libcrypto.dylib",
            "/usr/local/opt/openssl@3/lib/libcrypto.dylib",
        ]
    )

    # 3. Đường dẫn phổ biến trên Linux (Ubuntu/Debian/Fedora)
    candidates.extend(
        [
            "/lib/x86_64-linux-gnu/libcrypto.so.3",
            "/usr/lib/x86_64-linux-gnu/libcrypto.so.3",
            "/usr/lib64/libcrypto.so.3",
        ]
    )

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class _PureRipemd160:
    """Fallback RIPEMD-160 thuần Python (chuẩn ISO/IEC 10118-3) khi OpenSSL 3 tắt legacy ripemd160."""

    _KL = (0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xA953FD4E)
    _KR = (0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x7A6D76E9, 0x00000000)
    _RL = (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
        7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
        3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
        1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
        4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13,
    )
    _RR = (
        5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
        6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
        15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
        8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
        12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11,
    )
    _SL = (
        11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
        7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
        11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
        11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
        9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6,
    )
    _SR = (
        8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
        9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
        9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
        15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
        8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11,
    )

    def __init__(self, data: bytes = b"") -> None:
        self._buf = bytearray(data)

    def update(self, data: bytes) -> None:
        self._buf.extend(data)

    @staticmethod
    def _rol(x: int, n: int) -> int:
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    @staticmethod
    def _f(j: int, x: int, y: int, z: int) -> int:
        if j < 16:
            return x ^ y ^ z
        if j < 32:
            return (x & y) | (~x & z)
        if j < 48:
            return (x | (~y & 0xFFFFFFFF)) ^ z
        if j < 64:
            return (x & z) | (y & (~z & 0xFFFFFFFF))
        return x ^ (y | (~z & 0xFFFFFFFF))

    def digest(self) -> bytes:
        msg = bytearray(self._buf)
        orig_bits = (len(msg) * 8) & 0xFFFFFFFFFFFFFFFF
        msg.append(0x80)
        while (len(msg) % 64) != 56:
            msg.append(0x00)
        msg.extend(struct.pack("<Q", orig_bits))

        h0, h1, h2, h3, h4 = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0
        for offset in range(0, len(msg), 64):
            x = struct.unpack("<16I", msg[offset : offset + 64])
            al, bl, cl, dl, el = h0, h1, h2, h3, h4
            ar, br, cr, dr, er = h0, h1, h2, h3, h4
            for j in range(80):
                rnd = j >> 4
                tl = (al + self._f(j, bl, cl, dl) + x[self._RL[j]] + self._KL[rnd]) & 0xFFFFFFFF
                tl = (self._rol(tl, self._SL[j]) + el) & 0xFFFFFFFF
                al, el, dl, cl, bl = el, dl, self._rol(cl, 10), tl, al

                tr = (ar + self._f(79 - j, br, cr, dr) + x[self._RR[j]] + self._KR[rnd]) & 0xFFFFFFFF
                tr = (self._rol(tr, self._SR[j]) + er) & 0xFFFFFFFF
                ar, er, dr, cr, br = er, dr, self._rol(cr, 10), tr, ar

            t = (h1 + cl + dr) & 0xFFFFFFFF
            h1 = (h2 + dl + er) & 0xFFFFFFFF
            h2 = (h3 + el + ar) & 0xFFFFFFFF
            h3 = (h4 + al + br) & 0xFFFFFFFF
            h4 = (h0 + bl + cr) & 0xFFFFFFFF
            h0 = t

        return struct.pack("<5I", h0, h1, h2, h3, h4)

    def hexdigest(self) -> str:
        return self.digest().hex()


def ensure_bitcoinlib_compat() -> None:
    """Kích hoạt bản vá tương thích OpenSSL / RIPEMD-160 trước khi nạp `bitcoin.wallet`."""
    global _PATCHED
    if _PATCHED:
        return

    orig_find_library = ctypes.util.find_library
    fallback_crypto = _find_bundled_libcrypto()

    def _patched_find_library(name: str) -> Optional[str]:
        found = orig_find_library(name)
        if found:
            return found
        if name in ("ssl.35", "ssl", "libeay32", "crypto") and fallback_crypto:
            return fallback_crypto
        return None

    ctypes.util.find_library = _patched_find_library

    # Kiểm tra ripemd160 trong hashlib
    try:
        hashlib.new("ripemd160", b"test")
    except ValueError:
        orig_hashlib_new = hashlib.new

        def _patched_hashlib_new(name: str, data: bytes = b"", **kwargs):  # type: ignore[no-untyped-def]
            if name.lower() == "ripemd160":
                return _PureRipemd160(data)
            return orig_hashlib_new(name, data, **kwargs)

        hashlib.new = _patched_hashlib_new  # type: ignore[assignment]

    _PATCHED = True
