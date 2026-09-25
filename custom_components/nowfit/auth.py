"""Coordinated member authentication and single-flight relogin."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .client import MemberClient
from .exceptions import InvalidCredentials, SessionExpired


class SessionManager:
    def __init__(
        self,
        client: MemberClient,
        email: str,
        password: str | None,
        store_password: bool,
    ) -> None:
        self.client = client
        self.email = email
        self._password = password if store_password else None
        self.store_password = store_password
        self.generation = 0
        self._lock = asyncio.Lock()
        self._attempts: deque[datetime] = deque(maxlen=2)

    async def async_login(self, password: str, remember: bool = True) -> None:
        await self.client.async_login(self.email, password, remember)
        self.generation += 1
        if self.store_password:
            self._password = password

    async def async_recover(self, failed_generation: int) -> None:
        if failed_generation != self.generation:
            return
        async with self._lock:
            if failed_generation != self.generation:
                return
            if self._password is None:
                raise SessionExpired("reauth_required")
            now = datetime.now(ZoneInfo("UTC"))
            while self._attempts and now - self._attempts[0] > timedelta(minutes=30):
                self._attempts.popleft()
            if len(self._attempts) >= 2:
                raise SessionExpired("login_budget_exhausted")
            self._attempts.append(now)
            try:
                await self.async_login(self._password)
            except InvalidCredentials:
                self._password = None
                raise
