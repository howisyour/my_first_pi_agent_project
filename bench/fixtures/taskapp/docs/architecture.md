# Architecture

Request flow: `Client` → `taskapp.app.dispatch` → `ROUTE_REGISTRY` lookup → route handler →
service → repository → in-memory store. The handler returns `(status, payload)` and the route's
schema renders the payload.

## Adding an endpoint

An endpoint is only reachable when all three of these exist:

1. A handler function in `taskapp/routes/<module>.py`.
2. The response schema exported from `taskapp/schemas/__init__.py` (listed in `__all__`).
3. A `Route(...)` entry in `ROUTE_REGISTRY` in `taskapp/registry.py`.

## Constants

Code in `taskapp/routes/` and `taskapp/services/` must not contain numeric literals other than
`0`, `1` and `-1`. Put every other number in `taskapp/constants.py` and import it.

## Generated code

`taskapp/models_generated.py` is generated from `schema/models.json` by `scripts/gen_models.py`.
Do not edit it by hand; the checksum in `schema/models.lock` is verified by the quality gate.
