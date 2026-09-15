# AGENTS.md

## Definition of done
- Run `python scripts/check.py` and make sure it exits 0 before you finish.
  `python -m pytest` only runs unit tests; passing it does not mean the change is done.

## Adding an API endpoint (all three are required)
1. Handler in `taskapp/routes/<module>.py`, returning `(status, payload)`.
2. Export the response schema from `taskapp/schemas/__init__.py` and add it to `__all__`.
3. Add a `Route(...)` to `ROUTE_REGISTRY` in `taskapp/registry.py`.

## Errors
- Raise `AppError` subclasses from `taskapp/errors.py` (`NotFoundError`, `ValidationError`, ...)
  with a specific `code`. Never raise `ValueError`, `KeyError`, `Exception` from routes or services.

## Generated code
- Never edit `taskapp/models_generated.py`. Change `schema/models.json`, then run
  `python scripts/gen_models.py`.

## Constants
- No numeric literals other than 0, 1, -1 in `taskapp/routes/` or `taskapp/services/`.
  Add them to `taskapp/constants.py`.

## Contract tests
- `tests/contract/` needs the plugin: `python -m pytest -p taskapp_testing.plugin tests/contract`.

## Migrations
- Model changes follow `docs/migrations.md`.
