# taskapp

A tiny in-memory task tracker API. There is no web server: requests go through
`taskapp.app.Client`, which dispatches to the handlers listed in `taskapp/registry.py`.

## Layout

- `taskapp/routes/` – request handlers
- `taskapp/services/` – use cases and validation
- `taskapp/schemas/` – response schemas
- `taskapp/storage/` – in-memory storage and demo data
- `schema/` – model definitions (source of `taskapp/models_generated.py`)
- `migrations/` – numbered data migrations

## Running tests

```
python -m pytest
```

This runs the fast unit tests. The full quality gate that CI runs is described in
[docs/testing.md](docs/testing.md).

## Docs

- [Architecture](docs/architecture.md)
- [Testing](docs/testing.md)
- [Errors](docs/errors.md)
- [Migrations](docs/migrations.md)
