from enum import StrEnum


class ErrorKind(StrEnum):
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    AUTH = "auth"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    MALFORMED_RESPONSE = "malformed_response"
    PROTOCOL = "protocol"


class ProviderError(Exception):
    """Classified provider failure.

    ``str(error)`` is only the kind, so messages are safe to log and expose;
    ``detail`` carries a short internal explanation that must never contain
    payload contents or credentials.
    """

    def __init__(
        self, kind: ErrorKind, *, retry_after: float | None = None, detail: str | None = None
    ) -> None:
        super().__init__(kind.value)
        self.kind = kind
        self.retry_after = retry_after
        self.detail = detail

    @property
    def retryable(self) -> bool:
        return self.kind in {ErrorKind.TIMEOUT, ErrorKind.UNAVAILABLE, ErrorKind.RATE_LIMITED}


def classify(error: int | Exception, *, retry_after: float | None = None) -> ProviderError:
    if isinstance(error, ProviderError):
        return error
    if isinstance(error, TimeoutError) or error == 408:
        return ProviderError(ErrorKind.TIMEOUT)
    if isinstance(error, ConnectionError):
        return ProviderError(ErrorKind.UNAVAILABLE)
    if isinstance(error, ValueError):
        return ProviderError(ErrorKind.MALFORMED_RESPONSE)
    if isinstance(error, int):
        if error == 429:
            return ProviderError(ErrorKind.RATE_LIMITED, retry_after=retry_after)
        if error in {401, 403}:
            return ProviderError(ErrorKind.AUTH)
        if error == 404:
            return ProviderError(ErrorKind.NOT_FOUND)
        if 400 <= error < 500:
            return ProviderError(ErrorKind.INVALID_REQUEST)
        if 500 <= error < 600:
            return ProviderError(ErrorKind.UNAVAILABLE)
    return ProviderError(ErrorKind.PROTOCOL)
