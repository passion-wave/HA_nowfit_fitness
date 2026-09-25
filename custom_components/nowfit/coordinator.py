"""Independent source coordinators."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .auth import SessionManager
from .client import MemberClient, PublicClient, parse_retry_after
from .const import ACCOUNT_INTERVAL, HISTORY_INTERVAL, PUBLIC_INTERVAL, SOURCE_TIME_ZONE
from .exceptions import InvalidCredentials, NowFitError, ParseError, RateLimited, SessionExpired
from .models import (
    AccountSnapshot,
    Coverage,
    HistorySnapshot,
    OccupancySnapshot,
    SourceStatus,
)
from .training import normalize_visits

_LOGGER = logging.getLogger(__name__)


def _failure_status(error: NowFitError) -> SourceStatus:
    if isinstance(error, RateLimited):
        return SourceStatus.RATE_LIMITED
    if isinstance(error, ParseError):
        return SourceStatus.PARSE_ERROR
    if isinstance(error, (SessionExpired, InvalidCredentials)):
        return SourceStatus.AUTH_REQUIRED
    return SourceStatus.TEMPORARY_ERROR


class OccupancyCoordinator(DataUpdateCoordinator[OccupancySnapshot]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: PublicClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="NowFit studio occupancy",
            update_interval=PUBLIC_INTERVAL,
        )
        self.client = client
        self.last_attempt_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.source_status = SourceStatus.TEMPORARY_ERROR
        self.last_error: str | None = None
        self.next_retry: datetime | None = None

    async def _async_update_data(self) -> OccupancySnapshot:
        self.last_attempt_at = datetime.now(ZoneInfo("UTC"))
        try:
            clubs = await self.client.async_get_clubs()
        except NowFitError as err:
            self.source_status = _failure_status(err)
            self.last_error = type(err).__name__
            self.next_retry = (
                parse_retry_after(err.retry_after, datetime.now(ZoneInfo("UTC")))
                if isinstance(err, RateLimited)
                else None
            )
            raise UpdateFailed(type(err).__name__) from err
        self.last_success_at = datetime.now(ZoneInfo("UTC"))
        self.source_status = SourceStatus.READY
        self.last_error = None
        self.next_retry = None
        return OccupancySnapshot(clubs=clubs, fetched_at=self.last_success_at)


class AccountCoordinator(DataUpdateCoordinator[AccountSnapshot]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MemberClient,
        auth: SessionManager,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="NowFit account",
            update_interval=ACCOUNT_INTERVAL,
        )
        self.client = client
        self.auth = auth
        self.last_success_at: datetime | None = None
        self.source_status = SourceStatus.TEMPORARY_ERROR
        self.last_error: str | None = None
        self.next_retry: datetime | None = None

    async def _async_update_data(self) -> AccountSnapshot:
        generation = self.auth.generation
        try:
            data = await self.client.async_get_account()
        except SessionExpired:
            try:
                await self.auth.async_recover(generation)
                data = await self.client.async_get_account()
            except (SessionExpired, InvalidCredentials) as err:
                self.source_status = SourceStatus.AUTH_REQUIRED
                self.last_error = type(err).__name__
                raise ConfigEntryAuthFailed from err
        except NowFitError as err:
            self.source_status = _failure_status(err)
            self.last_error = type(err).__name__
            self.next_retry = (
                parse_retry_after(err.retry_after, datetime.now(ZoneInfo("UTC")))
                if isinstance(err, RateLimited)
                else None
            )
            raise UpdateFailed(type(err).__name__) from err
        self.last_success_at = data.fetched_at
        self.source_status = SourceStatus.READY
        self.last_error = None
        self.next_retry = None
        return data


class HistoryCoordinator(DataUpdateCoordinator[HistorySnapshot]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MemberClient,
        auth: SessionManager,
        minimum_duration: int,
        timezone: str = SOURCE_TIME_ZONE,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="NowFit history",
            update_interval=HISTORY_INTERVAL,
        )
        self.client = client
        self.auth = auth
        self.timezone = ZoneInfo(timezone)
        self.minimum_duration = minimum_duration
        self.last_success_at: datetime | None = None
        self.source_status = SourceStatus.TEMPORARY_ERROR
        self.last_error: str | None = None
        self.next_retry: datetime | None = None

    async def _async_update_data(self) -> HistorySnapshot:
        generation = self.auth.generation
        try:
            rows = await self.client.async_get_history(self.timezone)
        except SessionExpired:
            try:
                await self.auth.async_recover(generation)
                rows = await self.client.async_get_history(self.timezone)
            except (SessionExpired, InvalidCredentials) as err:
                self.source_status = SourceStatus.AUTH_REQUIRED
                self.last_error = type(err).__name__
                raise ConfigEntryAuthFailed from err
        except NowFitError as err:
            self.source_status = _failure_status(err)
            self.last_error = type(err).__name__
            self.next_retry = (
                parse_retry_after(err.retry_after, datetime.now(ZoneInfo("UTC")))
                if isinstance(err, RateLimited)
                else None
            )
            raise UpdateFailed(type(err).__name__) from err
        fetched_at = datetime.now(ZoneInfo("UTC"))
        self.last_success_at = fetched_at
        self.source_status = SourceStatus.READY
        self.last_error = None
        self.next_retry = None
        return normalize_visits(
            rows,
            fetched_at,
            minimum_duration=self.minimum_duration,
            coverage=Coverage.UNKNOWN,
        )
