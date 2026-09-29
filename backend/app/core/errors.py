from fastapi import Request
from fastapi.responses import ORJSONResponse
from starlette import status


class AppError(Exception):
    def __init__(self, detail: str, code: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.status_code = status_code


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Authentication required", code: str = "UNAUTHORIZED") -> None:
        super().__init__(detail, code, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Forbidden", code: str = "FORBIDDEN") -> None:
        super().__init__(detail, code, status.HTTP_403_FORBIDDEN)


class ConsentRequiredError(AppError):
    def __init__(self, detail: str = "Server processing consent required", code: str = "CONSENT_REQUIRED") -> None:
        super().__init__(detail, code, status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, detail: str, code: str = "CONFLICT") -> None:
        super().__init__(detail, code, status.HTTP_409_CONFLICT)


class RateLimitError(AppError):
    def __init__(self, detail: str = "Too many attempts", code: str = "RATE_LIMITED") -> None:
        super().__init__(detail, code, status.HTTP_429_TOO_MANY_REQUESTS)


class DailyLimitError(AppError):
    def __init__(self, detail: str = "Daily server processing limit reached", code: str = "DAILY_LIMIT") -> None:
        super().__init__(detail, code, status.HTTP_429_TOO_MANY_REQUESTS)


class BadRequestError(AppError):
    def __init__(self, detail: str, code: str = "BAD_REQUEST") -> None:
        super().__init__(detail, code, status.HTTP_400_BAD_REQUEST)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Not found", code: str = "NOT_FOUND") -> None:
        super().__init__(detail, code, status.HTTP_404_NOT_FOUND)


class PayloadTooLargeError(AppError):
    def __init__(self, detail: str = "Payload too large", code: str = "PAYLOAD_TOO_LARGE") -> None:
        super().__init__(detail, code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


async def app_error_handler(_: Request, exc: AppError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )
