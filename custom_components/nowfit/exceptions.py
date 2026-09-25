"""Explicit NowFit error taxonomy."""


class NowFitError(Exception):
    """Base exception."""


class CannotConnect(NowFitError):
    pass


class UpstreamUnavailable(NowFitError):
    pass


class RateLimited(NowFitError):
    def __init__(self, retry_after: str | None = None) -> None:
        super().__init__("rate_limited")
        self.retry_after = retry_after


class ParseError(NowFitError):
    pass


class UnsafeRedirect(NowFitError):
    pass


class UnexpectedContent(NowFitError):
    pass


class SessionExpired(NowFitError):
    pass


class InvalidCredentials(NowFitError):
    pass


class UnsupportedLogin(NowFitError):
    pass


class AccountMismatch(NowFitError):
    pass


class ClubNotFound(NowFitError):
    pass


class AmbiguousClub(NowFitError):
    pass
