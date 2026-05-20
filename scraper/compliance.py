from __future__ import annotations

from dataclasses import dataclass
import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


@dataclass(slots=True)
class CompliancePolicy:
    user_agent: str = "under-over-bot/0.1 (+contact: add-email-before-production)"
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 3.0
    timeout_seconds: float = 15.0


class ComplianceGuard:
    def __init__(self, policy: CompliancePolicy | None = None) -> None:
        self.policy = policy or CompliancePolicy()
        self._robots_cache: dict[str, RobotFileParser] = {}

    def wait_with_jitter(self) -> None:
        delay = random.uniform(self.policy.min_delay_seconds, self.policy.max_delay_seconds)
        time.sleep(delay)

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        base = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots_cache.get(base)
        if parser is None:
            parser = RobotFileParser()
            parser.set_url(f"{base}/robots.txt")
            try:
                parser.read()
            except Exception:
                # Fail closed for now: disallow when robots cannot be checked.
                return False
            self._robots_cache[base] = parser

        return parser.can_fetch(self.policy.user_agent, url)

    def build_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.policy.timeout_seconds,
            headers={"User-Agent": self.policy.user_agent},
            follow_redirects=True,
        )
