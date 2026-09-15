# Errors

Expected failures are raised as subclasses of `taskapp.errors.AppError`:

| Class | HTTP status |
| --- | --- |
| `ValidationError` | 422 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `PermissionDeniedError` | 403 |

Pass a specific machine-readable `code`, for example
`raise NotFoundError("project 7 not found", code="PROJECT_NOT_FOUND")`.

The dispatcher turns an `AppError` into `{"error": {"code": ..., "message": ...}}` with the class's
status. Any other exception becomes a 500 `INTERNAL_ERROR`, so never raise `ValueError`,
`KeyError`, `Exception` and similar built-ins from routes or services.
