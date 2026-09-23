"""Privacy helpers for analytics.

Raw IP addresses are never stored. They are pseudonymised with a salt that is
rotated on an interval, so hashes from different windows cannot be linked to
each other (and cannot be reversed to an address).
"""

from __future__ import annotations

import hashlib
import secrets
import time


class IPHasher:
    def __init__(self, reset_interval: int = 3600) -> None:
        self.init_ts: float = time.time()
        self.salt: str | None = None
        self.reset_interval: int = reset_interval

    def hash_ip(self, ip: str) -> str:
        """GDPR compliant hiding of the IP.

        The salt rotates every `reset_interval` seconds, which deliberately
        limits this to a per-window identifier rather than a long-lived one.
        """
        if self.salt is None or time.time() - self.init_ts > self.reset_interval:
            self.salt = secrets.token_hex(16)
            self.init_ts = time.time()
        return hashlib.sha256((ip + self.salt).encode()).hexdigest()


hasher = IPHasher()
