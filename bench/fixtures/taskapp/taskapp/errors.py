"""Application errors. Every expected failure is raised as an AppError subclass."""

from taskapp.constants import HTTP_CONFLICT, HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_UNPROCESSABLE


class AppError(Exception):
    status = HTTP_UNPROCESSABLE
    code = "APP_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status = HTTP_NOT_FOUND
    code = "NOT_FOUND"


class ValidationError(AppError):
    status = HTTP_UNPROCESSABLE
    code = "VALIDATION_ERROR"


class ConflictError(AppError):
    status = HTTP_CONFLICT
    code = "CONFLICT"


class PermissionDeniedError(AppError):
    status = HTTP_FORBIDDEN
    code = "PERMISSION_DENIED"
